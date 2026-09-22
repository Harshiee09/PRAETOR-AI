# PRAETOR AI Data Manifest and Blueprint

## Statutory Law & Legislation
- **India Code Portal (indiacode.nic.in / indiacode.gov.in)** – Official repository of central and state statutes, rules, and regulations. Central Acts of interest include, for example, the Indian Contract Act (1872), Civil Procedure Code (1908), Criminal Procedure Code (1973), Transfer of Property Act (1882), Registration Act (1908), and Consumer Protection Act (2019). (No public API; acts can be downloaded in PDF/HTML via India Code's web interface or its document IDs.)  
- **Legislative Department (legislative.gov.in)** – New Govt. portal for Acts of Parliament. Acts are stored in a DSpace (e.g. `/server/api/core/bitstreams/{UUID}/content` endpoints) and can be fetched programmatically if IDs are known.  
- **PRS India / Other Repositories** – Third-party sites (PRS India, BareActslive, etc.) provide text of central Acts. For machine ingestion, India Code (NIC) is authoritative.  
- **HuggingFace – Aalap Instruction (Statute data)** – Contains “Statute Ingredients” entries derived from popular sections of Indian Central Acts. e.g.:  
   ```json
   {
     "statutory_sources": [
       {
         "name": "India Code (NIC)",
         "url": "https://indiacode.nic.in/",
         "description": "Official bare-act text (PDF/HTML) for all Central and State acts."
       },
       {
         "name": "Legislative Dept (DSpace API)",
         "url": "https://legislative.gov.in/",
         "description": "Official Acts of Parliament via DSpace API (bitstream content)."
       },
       {
         "name": "Aalap – Statute Definitions",
         "url": "https://huggingface.co/datasets/opennyaiorg/aalap_instruction_dataset",
         "description": "Statute definition tasks from Indian Central Acts"
       }
     ]
   }
   ```  

## Landmark Judgments & Case Law
- **Constitutional & Property Law:** _Kesavananda Bharati v. State of Kerala_ (1973) – established the “basic structure” doctrine. Others include _Golaknath v. Punjab_ (1967) and _Minerva Mills v. Union of India_ (1980).  
- **Land & Property Disputes:** e.g. _Indore Dev. Auth. v. Manoharlal_ (2023, on land acquisition) and other land-acquisition/compensation cases. (Legal queries often use Act names like “land acquisition act ORR transfer of property act” to filter in Indian Kanoon.)  
- **Contract/Civil Law:** Key contract and civil cases (e.g. cases on the Indian Contract Act, Specific Relief Act, etc.).  
- **Consumer Law:** Notable consumer-Protection rulings (e.g. cases under the Consumer Protection Act).  
- **Data Extraction:** Use **Indian Kanoon API** for crawling judgments. The API provides full text and enriched metadata (each paragraph labeled with rhetorical roles – Facts, Issues, Arguments, Analysis, Conclusion – and extracted citations). For example, the OpenNyAI *InJudgements* corpus collected a representative 1950–2017 sample of Supreme Court/high court cases via Indian Kanoon searches. The dataset metadata even shows query keywords used for each domain (e.g. Land & Property queries in IndianKanoon).  
- **Structured List (sample):**  

  ```json
  "landmark_cases": [
    {
      "name": "Kesavananda Bharati v. State of Kerala",
      "year": 1973,
      "domain": "Constitution/Property",
      "notes": "Basic Structure doctrine case"
    },
    {
      "name": "Indore Development Authority v. Manoharlal",
      "year": 2023,
      "domain": "Land Acquisition/Property",
      "notes": "Land acquisition (RFCTLARR Act) interpretation case"
    },
    {
      "name": "Rama Krishna Agarwal v. ...",
      "year": 2009,
      "domain": "Consumer Rights",
      "notes": "Consumer protection (example)"
    }
  ]
  ```  

- **Metadata Sourcing:** Can scrape Supreme Court judgments from judis.nic.in or ecourts (PDFs/HTML) if available. Indian Kanoon’s APIs/search can tag judgments by subject via keywords. For example, InJudgements used act-name queries to ensure coverage across tax, criminal, civil, land, constitutional, etc.. Use citations (e.g. Indian Kanoon’s structured output) to classify segments of each judgment.

## Procedural Checklists & Templates
- **Government Portals:** State/National e-services portals often publish procedure manuals (e.g. registration processes) and citizen charters. For example, J&K’s Registration Dept Citizen Charter details land/doc registration rules (e.g. deeds must be registered within 4 months under Sec.23 of the 1908 Act). Similarly, various state “e-District” sites provide step-by-step application guidelines for services (property registration, utilities, etc.).  
- **Police Procedures:** Many states’ police sites or NRCB publications outline FIR and complaint filing procedures. In practice, one can scrape official police commission or home ministry PDF guides. The OpenNyAI Aalap corpus explicitly collected real FIR text from Maharashtra and Delhi police reports, which could be repurposed as examples of event descriptions for timeline checklists.  
- **Legal Aids:** Public databases (e.g. NALSA, Ministry of Law) publish legal aid forms and sample petition formats (e.g. consumer complaint forms, PIL templates). These can be downloaded from official sites.  
- **Data Examples:**  
  ```json
  "procedure_sources": [
    {
      "name": "J&K Reg. Dept Citizen Charter",
      "url": "https://igr.jk.gov.in/CitAreCitCharter.html",
      "notes": "Registration timelines and rules (e.g. 4-month rule under Sec.23)"
    },
    {
      "name": "OpenNyAI – FIR Dataset",
      "url": "https://huggingface.co/datasets/opennyaiorg/aalap_instruction_dataset",
      "notes": "Contains real FIRs from Maharashtra/Delhi police"
    }
  ]
  ```  

## Chunking & Indexing Strategy (GPU-Accelerated)
- **Data Download:** Use `datasets.load_dataset` (HuggingFace) or custom scripts to fetch texts. For example, load *InJudgements_dataset* via:  
  ```python
  from datasets import load_dataset
  judg = load_dataset("opennyaiorg/InJudgements_dataset", split="train")
  ```
- **Tokenizer & Text Splitter:** Use a tokenizer (e.g. HuggingFace `AutoTokenizer`) and LangChain’s text splitters. Example blueprint:  
  ```python
  from transformers import AutoTokenizer
  from langchain.text_splitter import RecursiveCharacterTextSplitter
  
  tokenizer = AutoTokenizer.from_pretrained("gpt2")
  splitter = RecursiveCharacterTextSplitter(
      chunk_size=512,
      chunk_overlap=50,
      tokenizer=tokenizer
  )
  ```
  This splits long legal texts into ~512-token chunks with ~50-token overlap to preserve context (good for Indian statutes/judgments). Adjust chunk_size (512–1024) as needed.  
- **Domain Folders:** Create folders for each domain (e.g. `./Land_Disputes`, `./Civil_Contracts`, `./Criminal_Procedure`) and save chunks accordingly:  
  ```python
  import os
  os.makedirs("data/Land_Disputes", exist_ok=True)
  # For each chunk in Land law text:
  with open(f"data/Land_Disputes/{doc_id}_chunk.txt", "w") as f:
      f.write(chunk_text)
  ```  
- **Vector Indexing (GPU):** Use a GPU-capable embedding model (e.g. a PyTorch Transformer or SentenceTransformer) to embed chunks. Example (using PyTorch on RTX 5070):  
  ```python
  from sentence_transformers import SentenceTransformer
  import torch
  model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
  embeddings = model.encode(chunks, convert_to_tensor=True)  # GPU
  ```
  Then build a vector index (e.g. FAISS with GPU support):  
  ```python
  import faiss
  dim = embeddings.shape[1]
  index = faiss.IndexFlatL2(dim)        # CPU index (or use faiss.IndexFlatIP with cuda)
  index.add(embeddings.cpu().numpy())   # move data back to CPU for FAISS
  ```  
- **Retrieval System:** Use LangChain or custom retrieval to query these indexes. For example, LangChain’s `FAISS` or `Chroma` vectorstores can load the chunks and support cosine similarity retrieval on GPU-embedded vectors.  

## Validation, Licensing & Storage Best Practices
- **Data Validation:** Check completeness and consistency. For statutory text, ensure entire sections are captured (no truncation). Verify that case law spans (outcome, headnotes) were correctly scraped. Use language/NER checks to spot missing citations or sections.  
- **Licensing:** Record and respect dataset licenses. Example: InJudgements_dataset is Apache-2.0 licensed; InLegalNER is MIT licensed; InRhetoricalRoles is Apache-2.0. Government texts (statutes, judgments) are generally public domain or open, but verify any portal terms. Always retain source citations (as we do here).  
- **Storage:** Store raw and processed data separately (e.g. raw JSON/CSV of scraped laws/cases, vs. chunked text). Use efficient formats (JSON or Parquet) with metadata fields. Maintain a local manifest (as above) mapping files to sources. Regularly back up to disk/SSD. For indexes, persist FAISS/Chroma stores on disk. Use encryption if needed for sensitive data (though public laws are not sensitive).  
- **Licensing Note:** Each data source entry in the manifest above includes its license (or notes). Before use, always check the latest license on the source site (e.g. HuggingFace dataset pages) and include an acknowledgement. For example, the InJudgements dataset explicitly lists Apache-2.0. 

**Sources:** India Code and legislative portals (official acts repository), Indian Kanoon API, HuggingFace OpenNyAI datasets (InJudgements, Aalap, InLegalNER, InRhetoricalRoles), and government citizen-charter examples. These inform the manifest structure and data extraction methods.