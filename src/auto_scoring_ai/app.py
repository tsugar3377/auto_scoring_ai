import streamlit as st
from markitdown import MarkItDown
import tempfile
import pytesseract
from pdf2image import convert_from_path
import boto3
import json
from botocore.exceptions import ClientError

def main():
    st.title("Auto Scoring AI")

    # サイドバーに問題文ファイルと模範解答ファイルのアップロードを配置
    st.sidebar.header("File Upload")
    question_file = st.sidebar.file_uploader("Upload file of exam questions", type=["pdf"])
    model_answer_file = st.sidebar.file_uploader("Upload file of model answer", type=["pdf"])

    if "contents_idx" not in st.session_state:
        st.session_state["contents_idx"] = 0
    if "contents_num" not in st.session_state:
        st.session_state["contents_num"] = 1

    form = st.sidebar.container()
    page = st.sidebar.columns(2)

    if question_file and model_answer_file:
        form.header("Answering")
        file_type = form.radio("chose file type", ["question", "answer"])
        if file_type == "question":
            contents = read_file(question_file)
        elif file_type == "answer":
            contents = read_file(model_answer_file)

        if page[1].button("Next page"):
            st.session_state.contents_idx = min(st.session_state.contents_num-1, st.session_state.contents_idx + 1)
        if page[0].button("Previous page"):
            st.session_state.contents_idx = max(0, st.session_state.contents_idx - 1)

        st.write(contents[st.session_state.contents_idx])

        with form.form("answer"):
            answer = st.text_area("Your answer")
            submitted = st.form_submit_button()

        st.session_state.contents_num = len(contents)
        
        if submitted:
            with st.spinner("Converting question to text..."):
                question_text = convert_image_to_text(question_file)
            with st.spinner("Converting answer to text..."):
                model_answer_text = convert_text_to_text(model_answer_file)
            response = auto_scoring(question_text, model_answer_text, answer)
            st.sidebar.header("Score")
            st.sidebar.write(response)


@st.cache_data
def read_file(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    if file_bytes is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name
                images = convert_from_path(tmp_file_path)
            return images
        except Exception as e:
            print(e)
            return None
    return None

@st.cache_data
def convert_text_to_text(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    if file_bytes is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name
                md = MarkItDown()
                result = md.convert(tmp_file_path)
            return result.text_content
        except Exception as e:
            print(e)
            return None
    return None

@st.cache_data
def convert_image_to_text(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    if file_bytes is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name
                images = convert_from_path(tmp_file_path)
                text = "\n".join([pytesseract.image_to_string(img, lang="jpn") for img in images])
            return text
        except Exception as e:
            print(e)
            return None
    return None

@st.cache_data
def auto_scoring(question, model_answer, answer):
    try:
        bedrock_runtime = boto3.client(service_name='bedrock-runtime')

        model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        system_prompt = "あなたは優秀な試験採点者です。"
        max_tokens = 1000

        # Prompt with user turn only.
        content = f'''
## あなたのタスク
以下の問題文と模範解答をもとに、ユーザーの回答を採点してください。
採点結果は設問ごとの点数(100点満点)とその理由を出力してください。

## 問題文
問1. 以下の設問に回答してください。
設問1: 日本で一番高い山を答えてください。
設問2: 日本で一番広い湖を答えてください。
設問3: 日本で二番目に高い山と日本で二番目に広い湖を答えてください。
## 模範解答
問1. 
設問1: 富士山
設問2: 琵琶湖
設問3: 北岳と霞ヶ浦
## ユーザーの回答
問1. 
設問1: 富士山
設問2: 霞ヶ浦
設問3: 北岳と浜名湖
## 採点結果
### 問1
- 設問1
  - 点数: 100
  - 理由: 答えが完全にあっているため
- 設問2
  - 点数: 0
  - 理由: 答えが完全に間違っているため
- 設問3
  - 点数: 50
  - 理由: 北岳のみ正解しているため

## 問題文
{question}
## 模範解答
{model_answer}
## ユーザーの回答
{answer}
## 採点結果
'''
        user_message =  {"role": "user", "content": content}
        messages = [user_message]

        response = generate_message (bedrock_runtime, model_id, system_prompt, messages, max_tokens)
        return response
        
    except ClientError as err:
        message=err.response["Error"]["Message"]
        print("A client error occured: " +
            format(message))
        return None
    

def generate_message(bedrock_runtime, model_id, system_prompt, messages, max_tokens):

    body=json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages
        }  
    )  

    
    response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
    response_body = json.loads(response.get('body').read())
   
    return response_body["content"][0]["text"]

if __name__ == "__main__":
    main()
