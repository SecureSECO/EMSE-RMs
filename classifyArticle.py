import os
import openai
import pypdf
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from article import Article
from criteria import CriteriaStore

from habanero import Crossref


# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure NLTK dependencies are available
nltk.download('punkt')

# 📌 Define research method categories
RESEARCH_METHODS = [
    "Data Science"
    "Engineering Research",
    "Design Science",
    "Experiments",
    "Grounded Theory",
    "Longitudinal",
    "Meta Science",
    "Optimization",
    "Qualitative Survey",
    "Quantitative Survey",
    "Quantitative Simulation",
    "Qualitative Simulation",
    "Questionnaire Survey",
    "Replication",
    "Repository Mining",
    "Systematic Review"
]


def extract_text_from_pdf(pdf_path, max_chars=4000):
    """Extracts text from a PDF file, limiting to max_chars for efficiency."""
    pdf_reader = pypdf.PdfReader(pdf_path)
    text = ""

    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"

    # Tokenize and limit the text length
    sentences = sent_tokenize(text)
    trimmed_text = " ".join(sentences[:max_chars // 20])  # Approximate sentence count

    return trimmed_text

def classify_research_method(pdf_path, model="gpt-4-turbo"):
    """Classifies a research article using OpenAI GPT API (Latest Version)."""
    # Step 1: Extract text from PDF
    article_text = extract_text_from_pdf(pdf_path)

    # Step 2: Construct structured prompt
    prompt = f"""
    Please classify the following text into one of the following research methods:
    {", ".join(RESEARCH_METHODS)}.
    
    Please provide your result as follows:
    Title: The article's title
    Resulting Method: The resulting method. If you do not find a result, please return "mixed method".
    
    Do not return anything else.

    Article Text:
    {article_text}
    
    """

    # Step 3: Initialize OpenAI client correctly
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Step 4: Call OpenAI API
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def get_doi_by_title(title):
    """
    Searches for a DOI based on an article title using the Crossref API via the habanero package.
    :param title: The title of the article.
    :return: The DOI if found, otherwise None.
    """
    cr = Crossref()
    results = cr.works(query_bibliographic=title, rows=1)
    
    if results['message']['items']:
        return results['message']['items'][0].get('DOI')
    
    return None

# Example usage


# 🔥 Run classification on a PDF

directory = "./articles/"
assistant_id = "asst_UqLB2dxyKWFXqrpTHMh05Eai"

for filename in os.listdir(directory):
    if not filename.lower().endswith(".pdf"):
        continue  # Skip non-PDF files

    filepath = os.path.join(directory, filename)
    print(f"\n📄 Processing: {filepath}")

    # 🔥 Step 1: Start a new OpenAI thread for this article
    thread = openai.beta.threads.create()
    thread_id = thread.id
    print(f"✅ New Thread Created: {thread_id}")

    # 🔹 Step 2: Extract a small portion of the PDF for title detection
    pdf_excerpt = extract_text_from_pdf(filepath, max_chars=1000)

    # 🔥 Step 3: Ask OpenAI for the title
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=f"Extract the title from this research paper:\n\n{pdf_excerpt}\n\nReturn only: Title: <title>"
    )

    # 🔄 Run the assistant
    run = openai.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

    # ⏳ Wait for OpenAI to process
    while run.status in ["queued", "in_progress"]:
        run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    # 🔥 Retrieve the title
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    title_response = messages.data[0].content[0].text.value
    title = title_response.replace("Title: ", "").strip()
    print(f"🔹 Extracted Title: {title}")

    # 🔍 Step 4: Check if DOI exists in Firestore
    try: 
        doi = get_doi_by_title(title)
    except:
        print("DOI retrieval failed, let's try once more.")
        doi = get_doi_by_title(title)
        
    if not doi:
        print("❌ Sorry, article's DOI not found by title...")
    else:
        print(f"✅ DOI found: {doi}")
        if Article.does_doi_exist(doi): # in DB
            print(f"Article already in DB, no need to extract RM")
            resulting_method = ""
        else:
            # 🔥 Step 5: Extract more of the PDF for research method classification
            pdf_excerpt_longer = extract_text_from_pdf(filepath, max_chars=5000)

        # 🔥 Ask OpenAI for the research method
            openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=f"Classify the research method of this research paper, based on exactly these research methods {", ".join(RESEARCH_METHODS)}. :\n\n{pdf_excerpt_longer}\n\nReturn only: Resulting Method: <method>"
            )

            # 🔄 Run the assistant again
            run = openai.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

            # ⏳ Wait for completion
            while run.status in ["queued", "in_progress"]:
                run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

            # 🔥 Retrieve the research method
            messages = openai.beta.threads.messages.list(thread_id=thread_id)
            method_response = messages.data[0].content[0].text.value
            resulting_method = method_response.replace("Resulting Method: ", "").strip()
            print(f"🔹 Extracted Research Method: {resulting_method}")
            
            # Here comes the big old set of questions for the resulting method
            criteria_store = CriteriaStore()
            criteria = criteria_store.is_criteria_available(resulting_method )
            rmQuality = ""
            
            if criteria:
                print(f"\n✅ Criteria for {resulting_method}:")
                for c in criteria:
                        prompt = criteria_store.generate_prompt_for_criterion(resulting_method, c['description'])
                        print(f"\n📌 Sending to OpenAI: {prompt}")

                        # 🔥 Send a single prompt to OpenAI
                        openai.beta.threads.messages.create(
                            thread_id=thread_id,
                            role="user",
                            content=prompt
                        )

                        # 🔄 Run the assistant for just this one criterion
                        run = openai.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

                        # ⏳ Wait for OpenAI to complete processing
                        while run.status in ["queued", "in_progress"]:
                            run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

                        # 🔥 Retrieve the response
                        messages = openai.beta.threads.messages.list(thread_id=thread_id)
                        assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]

                        if assistant_messages:
                            latest_message = max(assistant_messages, key=lambda msg: msg.created_at)  # Get the latest by timestamp
                            print(latest_message)
                            response_text = latest_message.content[0].text.value.strip()
    
                            yes_no_answer = response_text.split("\n")[-1].strip()  # Extract last line (Yes/No)
    
                            if yes_no_answer not in ["Yes", "No"]:
                                yes_no_answer = "Unknown"
                        else:
                            yes_no_answer = "Unknown"
                        # Store result
                        rmQuality += f"{c['description']} {yes_no_answer}\n"
                        
                        print(f"✅ Extracted: ({c['description']}, {yes_no_answer})")

                else:
                    print(f"\n❌ No criteria found for {resulting_method}.")
                    
            

    # 🔹 Step 6: Store the article in Firestore
            article = Article(
                name=title,
                research_method=resulting_method,
                doi=doi if doi else "no doi",
                articleQuality={},
                rmQuality=rmQuality,
                filenames={filename}
            )

            article.save_to_firestore()

    # 🔥 Step 7: Close the OpenAI thread (optional)
    final_run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    token_usage = final_run.usage  # Contains token info
    print(final_run.usage)

    openai.beta.threads.delete(thread_id)
    print(f"✅ Thread {thread_id} closed.")