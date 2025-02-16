import pytest
import boto3
from auto_scoring_ai.app import generate_message, auto_scoring

class TestAutoScoring():
    def setup_method(self):
        pass

    @pytest.mark.parametrize("content", [("日本で一番高い山を教えてください。")])
    def test_generate_message(self, content):
        bedrock_runtime = boto3.client(service_name='bedrock-runtime')

        model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        system_prompt = "あなたは優秀なAIアシスタントです。"
        max_tokens = 1000
        user_message =  {"role": "user", "content": "日本で一番高い山を教えてください。"}
        messages = [user_message]

        response = generate_message(bedrock_runtime, model_id, system_prompt, messages, max_tokens)
        print(response)
        assert response

    @pytest.mark.parametrize(
            "question, model_answer, answer", 
            [
                (
                    "日本で一番深い湖を答えてください。",
                    "田沢湖",
                    "田沢湖です。",
                ),
                (
                    "日本で一番深い湖を答えてください。",
                    "田沢湖",
                    "琵琶湖です。",
                ),
                (
                    "大人より子供のほうが学習能力が高いという主張は正しいですか？",
                    "この主張は、一部の面で正しいとされていますが、完全に正しいとは言い切れません。実際には、年齢や状況によって異なる要素が関与しています。",
                    "この主張は正しいです。",
                ),
            ]
        )
    def test_auto_scoring(self, question, model_answer, answer):
        response = auto_scoring(question, model_answer, answer)
        print(response)
        assert response