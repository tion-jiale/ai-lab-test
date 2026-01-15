import streamlit as st
import nltk
from PyPDF2 import PdfReader

# Ensure punkt tokenizer is available
nltk.download("punkt", quiet=True)

# Streamlit page config
st.set_page_config(
    page_title="PDF Sentence Chunker (NLTK)",
    layout="wide"
)

st.title("PDF Sentence Chunker Demo")

st.write(
    "Upload a PDF file, extract text, and split it into sentences using "
    "NLTK's `sent_tokenize`. A sample of sentences (indices 58–68) is shown below."
)

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    try:
        # Read PDF
        reader = PdfReader(uploaded_file)
        pages_text = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages_text.append(page_text)

        full_text = " ".join(pages_text).strip()

        # Basic info
        st.subheader("Basic info")
        st.write(f"Number of pages: **{len(reader.pages)}**")
        st.write(f"Total characters extracted: **{len(full_text)}**")

        if not full_text:
            st.warning("No text could be extracted from this PDF.")
        else:
            # Sentence tokenization
            sentences = nltk.sent_tokenize(full_text)

            st.success(f"Number of detected sentences: {len(sentences)}")

            # Display sample sentences 58–68
            st.subheader("Sample sentences (indices 58–68)")

            if len(sentences) >= 59:
                start = 58
                end = min(68, len(sentences))

                for i in range(start, end):
                    st.markdown(f"**{i}**. {sentences[i]}")
            else:
                st.warning(
                    "The document does not contain enough sentences "
                    "to display indices 58–68."
                )

            # Optional interactive viewer
            st.subheader("Browse sentences")
            start_idx = st.number_input(
                "Show sentences starting from index",
                min_value=0,
                max_value=max(len(sentences) - 1, 0),
                value=0,
                step=1,
            )

            end_idx = st.number_input(
                "Up to (exclusive)",
                min_value=start_idx + 1,
                max_value=len(sentences),
                value=min(start_idx + 10, len(sentences)),
                step=1,
            )

            for i in range(start_idx, end_idx):
                st.markdown(f"**{i}**. {sentences[i]}")

    except Exception as e:
        st.error(f"Error reading PDF: {e}")

else:
    st.info("Please upload a PDF to begin.")
