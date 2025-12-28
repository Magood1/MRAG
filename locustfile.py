from locust import HttpUser, task, between

class MRAGUser(HttpUser):
    # وقت انتظار عشوائي بين الطلبات (1 إلى 3 ثواني)
    wait_time = between(1, 3)

    @task
    def chat_test(self):
        headers = {"X-API-Key": "secret-key-123"}
        payload = {
            "kb_id": "test1",
            "query": "ما هي سياسات العمل؟"
        }
        
        # نستخدم catch_response للتحكم في كيفية اعتبار الطلب ناجحًا أو فاشلاً
        with self.client.post("/api/v1/assistant/chat", json=payload, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # نعتبر تجاوز الحد (Rate Limit) نجاحًا لاختبار الحماية
                response.success() 
            else:
                response.failure(f"Failed with status code {response.status_code}: {response.text}")
                