import json
import os
import boto3

# 初始化 Bedrock Runtime Client
bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-southeast-2')

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # 檢查這是不是來自 S3 的觸發事件
        if 'Records' in event and event['Records'][0]['eventSource'] == 'aws:s3':
            # 解析 S3 事件中的 Bucket 與 File Key
            s3_record = event['Records'][0]['s3']
            bucket_name = s3_record['bucket']['name']
            file_key = s3_record['object']['key']
            
            print(f"收到 S3 新檔案通知！Bucket: {bucket_name}, File: {file_key}")
            
              # 如果上傳的剛好是向量資料夾本身，直接跳過避免無限循環
            if file_key.startswith('vectors/'):
                return {'statusCode': 200, 'body': 'Skipped vector file'}

            # 從 S3 讀取該檔案的內容
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            file_content = response['Body'].read().decode('utf-8')
            
            # 這裡可以呼叫我們剛剛寫的 chunk_text 進行切片！
            chunk_size = 500
            chunks = [
                file_content[i : i + chunk_size]
                for i in range(0, len(file_content), chunk_size)
            ]

            vector_records = []

            #  迴圈處理每一個 Chunk，呼叫 Bedrock 轉成向量
            for idx, chunk in enumerate(chunks):

                embedding_vector = get_text_embedding(chunk)

                vector_records.append({
                    'chunk_id': f'{file_key}_chunk_{idx}',
                    'text': chunk,
                    'embedding': embedding_vector,
                    'metadata': {'source': file_key, 'chunk_index': idx},
                })

            # 將所有向量資料打包成 JSON，存回同一個 S3 Bucket 的 vectors/ 資料夾下
            output_key = f"vectors/{file_key}.json"

            s3_client.put_object(
                Bucket=bucket_name,
                Key=output_key,
                Body=json.dumps(vector_records, ensure_ascii=False),
                ContentType='application/json',
            )

            print(f'向量資料已成功存入 S3: {output_key}')

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'message': f'Successfully processed file {file_key} from S3.'
                })
            }
            
    except Exception as e:
        print(f"Error processing S3 event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }

def get_text_embedding(text_chunk):
    """
    呼叫 Amazon Bedrock 的 Embedding 模型，將文字轉成向量 (Vector)
    """
    model_id = "amazon.titan-embed-text-v2:0"  # Amazon Titan 向量化模型 ID
    
    # 建構 Embedding 的請求 Payload
    native_request = {
        "inputText": text_chunk,
        "dimensions": 1024,  # 設定向量維度大小
        "normalize": True
    }
    
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(native_request)
    )
    
    model_response = json.loads(response['body'].read())
    
    # 回傳這段文字的向量數據（一串浮點數列表）
    return model_response.get("embedding")

def process_document_from_s3(file_content):
    """
    完整流程示範：切片 -> 向量化
    """
    # 1. 先切片 (Chunking)
    chunks = chunk_text(file_content, chunk_size=500, chunk_overlap=50)
    
    embedded_chunks = []
    
    # 2. 逐一送去 Embedding 模型轉換成向量
    for i, chunk in enumerate(chunks):
        vector = get_text_embedding(chunk)
        
        embedded_chunks.append({
            "chunk_id": i,
            "text": chunk,
            "vector": vector  # 這就是轉好的向量，準備存入向量資料庫
        })
        print(f"已完成第 {i+1} 個 Chunk 的向量化處理！")
        
    return embedded_chunks

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    """
    將長文本切片成帶有重疊區塊的 chunks
    :param text: 原始長文本
    :param chunk_size: 每個 chunk 的最大字元數
    :param chunk_overlap: 相鄰 chunk 之間的重疊字元數
    :return: 切片後的文字列表
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        
        # 移動指針，保留 overlap 空間
        if end == text_length:
            break
        start += chunk_size - chunk_overlap

    return chunks

# 測試範例：
sample_text = "這是一篇關於企業知識庫的長篇報告。第一段介紹了系統的架構設計。第二段說明了安全性與 IAM 權限控管。第三段則探討了透過 Amazon Bedrock 實現高效能 AI 生成的具體方式。"
result_chunks = chunk_text(sample_text, chunk_size=30, chunk_overlap=5)

for i, chunk in enumerate(result_chunks):
    print(f"Chunk {i+1}: {chunk}")