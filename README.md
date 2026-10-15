# aws-serverless-rag-assistant
An enterprise-grade, fully serverless RAG knowledge assistant built on AWS, leveraging large language models (LLMs) via Amazon Bedrock to deliver context-aware, hallucination-reduced AI responses based on custom document repositories.

---

## 📐 System Architecture Diagram
*(請將你的 AWS 架構圖 PNG 檔上傳至專案中，並在此處替換圖片路徑)*
![Architecture Diagram](./architecture.png)

---

## 🚀 Key Architectural Highlights

1. **Serverless Generative AI Pipeline:**
   - Powered by **AWS Bedrock** (utilizing advanced foundation models such as **Amazon Nova Pro**) to generate secure, high-quality, and contextually accurate natural language responses.
2. **Asynchronous Ingestion & Document Processing:**
   - Built a scalable backend ingestion pipeline using **Amazon S3**, **AWS Lambda**, and **API Gateway** to securely process unstructured documents, manage text chunking, and handle semantic queries efficiently.
3. **Optimized Full-Stack User Experience:**
   - Developed a responsive, real-time single-page application (SPA) using **React** and **Vite**, supporting conversational streaming and interactive knowledge queries.
4. **Cloud-Native Static Hosting & Security:**
   - Securely deployed the frontend via **Amazon S3** and **Amazon CloudFront** using **Origin Access Control (OAC)** to enforce least-privilege access and global low-latency content delivery.
5. **Infrastructure as Code (IaC):**
   - Entire cloud environment and resource bindings are fully provisioned and managed using **AWS CloudFormation**, ensuring reproducible and maintainable infrastructure deployments.

---

## 🛠️ Tech Stack
- **Cloud / AI / AWS:** Amazon Bedrock (Amazon Nova Pro), AWS Lambda, Amazon API Gateway, Amazon S3, Amazon CloudFront (with OAC), CloudFormation
- **Backend:** Python, Boto3, LangChain / Vector Embeddings (視乎你的實作細節可自行微調)
- **Frontend:** React, Vite, JavaScript
- **Architecture:** Serverless, RAG (Retrieval-Augmented Generation), Event-Driven API
