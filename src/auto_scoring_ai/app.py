import streamlit as st
from markitdown import MarkItDown
import tempfile
import pytesseract
from pdf2image import convert_from_path

def main():
    st.title("Auto Scoring AI")

    form = st.sidebar.container()
    page_button = st.sidebar.columns(2)

    # サイドバーに問題文ファイルと模範解答ファイルのアップロードを配置
    st.sidebar.header("File Upload")
    question_file = st.sidebar.file_uploader("Upload file of exam questions", type=["pdf"])
    answer_file = st.sidebar.file_uploader("Upload file of model answer", type=["pdf"])

    if "contents_idx" not in st.session_state:
        st.session_state["contents_idx"] = 0
    if "contents_num" not in st.session_state:
        st.session_state["contents_num"] = 1
    if page_button[1].button("Next page"):
        st.session_state.contents_idx = min(st.session_state.contents_num-1, st.session_state.contents_idx + 1)
    if page_button[0].button("Previous page"):
        st.session_state.contents_idx = max(0, st.session_state.contents_idx - 1)

    if question_file and answer_file:
        form.header("Answering")
        file_type = form.radio("chose file type", ["question", "answer"])
        if file_type == "question":
            contents = read_file(question_file)
        elif file_type == "answer":
            contents = read_file(answer_file)

        st.session_state.contents_num = len(contents)
        st.session_state.contents_idx = min(st.session_state.contents_num-1, st.session_state.contents_idx)
        st.write(contents[st.session_state.contents_idx])
        with form.form("answer"):
            answer = st.text_area("Your answer")
            submitted = st.form_submit_button()
        
        if submitted:
            question_text = convert_image_to_text(question_file)
            answer_text = convert_text_to_text(answer_file)
            pass


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

if __name__ == "__main__":
    main()
