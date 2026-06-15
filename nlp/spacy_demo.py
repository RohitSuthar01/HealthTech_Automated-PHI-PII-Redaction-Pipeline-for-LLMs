import spacy

def main():
    # Load the English spaCy language model
    # en_core_web_sm is a small, efficient model that handles named entity recognition (NER)
    print("Loading spaCy model 'en_core_web_sm'...")
    nlp = spacy.load("en_core_web_sm")
    
    # A sample clinical note featuring various names, locations, dates, and medical terms
    sample_text = (
        "Patient John Smith, a 45-year-old male, was admitted to Sunrise Hospital on 05/06/2026. "
        "He was referred by Dr. Emily Carter. He resides at 42 MG Road, Mumbai, Maharashtra. "
        "The patient complains of a persistent cough, which he suspects might be bronchitis."
    )
    
    print("\n" + "="*80)
    # Process the text using the NLP pipeline
    # spaCy automatically tokenizes, tags, parses, and identifies entities in the text
    doc = nlp(sample_text)
    
    print(f"ORIGINAL TEXT:\n{sample_text}")
    print("="*80)
    
    print("\nDETECTED ENTITIES (spaCy NER):")
    # doc.ents is a tuple of identified Span objects representing entities
    for ent in doc.ents:
        # ent.text is the substring, ent.label_ is the type (e.g., PERSON, ORG, GPE, DATE)
        print(f"  -> Entity: '{ent.text}' | Label: {ent.label_} ({spacy.explain(ent.label_)}) | Position: [{ent.start_char}:{ent.end_char}]")
    
    print("\nUNDERSTANDING SPACY TOKENS & NER:")
    print("  1. 'doc.ents' provides identified entities as Span objects.")
    print("  2. 'ent.label_' gives the category of the entity.")
    print("  3. For finding patient names, we look specifically for the 'PERSON' label.")
    print("  4. Notice how medical terms like 'cough' or 'bronchitis' are NOT highlighted, "
          "as they are conditions/symptoms, not identifiers.")
    print("="*80)

if __name__ == "__main__":
    main()
