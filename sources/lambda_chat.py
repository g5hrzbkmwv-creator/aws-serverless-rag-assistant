import json
import os
import boto3
import math  # 用 python 內建的 math 取代 numpy

# 初始化 Bedrock Runtime Client
bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-southeast-2')
s3_client = boto3.client('s3')

# 從環境變數讀取 S3 桶名 (確保在 CloudFormation 有設定 DOCUMENT_BUCKET_NAME)
BUCKET_NAME = os.environ.get('DOCUMENT_BUCKET_NAME')

def get_embedding(text):
  """將使用者的問題轉為向量 (使用 Titan Embeddings)"""
  model_id = "amazon.titan-embed-text-v2:0"  # 或 titan-embed-text-v2:0
  payload = {"inputText": text}

  response = bedrock_runtime.invoke_model(
      modelId=model_id,
      contentType="application/json",
      accept="application/json",
      body=json.dumps(payload),
  )
  return json.loads(response["body"].read())["embedding"]


def cosine_similarity(a, b):
  """計算兩個向量之間的餘弦相似度"""
  dot_product = sum(x * y for x, y in zip(a, b))
  magnitude_a = math.sqrt(sum(x * x for x in a))
  magnitude_b = math.sqrt(sum(y * y for y in b))
  if magnitude_a == 0 or magnitude_b == 0:
    return 0.0
  return dot_product / (magnitude_a * magnitude_b)


def load_all_vectors_from_s3(bucket_name):
  """從 S3 的 vectors/ 資料夾載入所有知識庫向量"""
  if not bucket_name:
    print("Warning: DOCUMENT_BUCKET_NAME environment variable not set.")
    return []

  all_chunks = []
  paginator = s3_client.get_paginator("list_objects_v2")

  for page in paginator.paginate(Bucket=bucket_name, Prefix="vectors/"):
    if "Contents" not in page:
      continue
    for obj in page["Contents"]:
      key = obj["Key"]
      if key.endswith(".json"):
        file_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        chunks = json.loads(file_obj["Body"].read().decode("utf-8"))
        all_chunks.extend(chunks)

  return all_chunks

def lambda_handler(event, context):
    try:

        # 1. 解析從前端或 Test 傳進來的請求 Body
        body = json.loads(event.get('body', '{}'))
        user_question = body.get('question', 'Hello, tell me about this system.')

        print(f"收到使用者問題: {user_question}")

        # 2. RAG 核心：向量檢索 (Retrieval)
        context_text = "No relevant information was found in the knowledge base."
        sources_count = 0

        if BUCKET_NAME:
            try:
                # 將問題轉成向量
                query_vector = get_embedding(user_question)

                # 從 S3 載入所有向量資料
                all_chunks = load_all_vectors_from_s3(BUCKET_NAME)

                if all_chunks:
                    # 計算相似度並排序
                    scored_chunks = []
                    for chunk in all_chunks:
                        chunk_vector = chunk['embedding']
                        score = cosine_similarity(query_vector, chunk_vector)
                        scored_chunks.append((score, chunk["text"]))

                    scored_chunks.sort(key=lambda x: x[0], reverse=True)
                    top_k_chunks = scored_chunks[:3]  # 取前 3 個最相關片段
                    sources_count = len(top_k_chunks)

                    context_text = "\n\n".join([
                        f"[Related fragments {i+1}]: {text}"
                        for i, (_, text) in enumerate(top_k_chunks)
                    ])
            except Exception as search_err:
                print(f"Vector search warning: {str(search_err)}")

        # 3. 使用 Amazon Nova Pro 模型 ID
        model_id = "amazon.nova-pro-v1:0"

        # 4. 結合檢索到的 Context 與使用者問題，建構 Amazon Nova 的請求 Payload
        prompt_content = f"""You are an enterprise-level RAG assistant. Please answer the questions based on the internal knowledge base provided below. If the knowledge base is insufficient to answer the question, please honestly admit that you do not know, and do not make things up.

    【Knowledge base content】
    {context_text}

    【User question】
    {user_question}"""

        # Amazon Nova 的正確請求 Payload 格式
        native_request = {
            "schemaVersion": "messages-v1",
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt_content}]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": 512,
                "temperature": 0.7
            }
        }

        # 呼叫 Amazon Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(native_request)
        )

        # 解析 Amazon Nova 的回傳結果結構
        model_response = json.loads(response['body'].read())
        
        # Nova 的標準回傳路徑：output -> message -> content -> [0] -> text
        answer = model_response['output']['message']['content'][0]['text']

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # 正式環境可替換為 CloudFront 網域
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',
            },
            'body': json.dumps({
                'status': 'success',
                'question': user_question,
                'answer': answer,
                "sources_used": sources_count
            }, ensure_ascii=False)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }

