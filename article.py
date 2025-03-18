import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firebase (if not already initialized)
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("firebase-key.json")  # 🔹 Path to your Firebase key
    firebase_admin.initialize_app(cred)

# Firestore connection
db = firestore.client()

class Article:
    """Represents a research article with metadata and Firestore integration."""

    def __init__(self, name: str, research_method: str, doi: str, articleQuality: dict, rmQuality: dict, filenames: set = None):
        """
        Initializes an Article object.

        :param name: Title of the article
        :param research_method: Classified research method
        :param doi: Digital Object Identifier (DOI)
        :param articleQuality: Generic JSON field 1
        :param rmQuality: Generic JSON field 2
        :param filenames: Set of filenames linked to the article
        """
        self.name = name
        self.research_method = research_method
        self.doi = doi
        self.articleQuality = articleQuality
        self.rmQuality = rmQuality
        self.filenames = filenames if filenames else set()

    def add_filename(self, filename: str):
        """Adds a filename to the set."""
        self.filenames.add(filename)

    def remove_filename(self, filename: str):
        """Removes a filename if it exists."""
        self.filenames.discard(filename)

    def to_dict(self):
        """Converts the Article object into a dictionary for Firestore storage."""
        return {
            "name": self.name,
            "research_method": self.research_method,
            "doi": self.doi,
            "articleQuality": self.articleQuality,
            "rmQuality": self.rmQuality,
            "filenames": list(self.filenames)  # Convert set to list for Firestore
        }

    @classmethod
    def from_dict(cls, data):
        """Creates an Article object from a Firestore document dictionary."""
        return cls(
            name=data["name"],
            research_method=data["research_method"],
            doi=data["doi"],
            articleQuality=data["articleQuality"],
            rmQuality=data["rmQuality"],
            filenames=set(data["filenames"])
        )

    def save_to_firestore(self):
        """Saves the Article object to Firestore. Prevents overwriting if DOI already exists."""
        articles_ref = db.collection("Articles")
    
        # 🔹 Check if a document with this DOI already exists
        existing_docs = articles_ref.where("doi", "==", self.doi).stream()
    
        for doc in existing_docs:
            # ✅ If a matching DOI is found, update the existing entry instead of overwriting
            doc_ref = articles_ref.document(doc.id)  # Keep the existing document ID
            doc_ref.update(self.to_dict())  # Update only new fields
            print(f"🔄 Updated existing article with DOI '{self.doi}' in Firestore.")
            return  # Stop execution since the update is done

        # 🆕 If no matching DOI is found, create a new document
        doc_ref = articles_ref.document(self.name)
        doc_ref.set(self.to_dict())  # Create a new entry
        print(f"✅ Article '{self.name}' saved to Firestore.")
    
    
    @staticmethod
    def does_doi_exist(doi: str) -> bool:
        """
        Checks whether a particular DOI is already in the Firestore database.

        :param doi: The DOI to check
        :return: True if DOI exists, False otherwise
        """
        # 🔥 Query Firestore for articles with the given DOI
        docs = db.collection("Articles").where("doi", "==", doi).stream()

        for doc in docs:
            return True  # ✅ DOI found, return True
        return False  # ❌ DOI not found, return False
            
    @classmethod
    def load_from_firestore(cls, name):
        """Retrieves an Article from Firestore."""
        doc_ref = db.collection("Articles").document(name)
        doc = doc_ref.get()
        if doc.exists:
            return cls.from_dict(doc.to_dict())
        else:
            print(f"❌ Article '{name}' not found in Firestore.")
            return None

    def update_firestore(self):
        """Updates an existing Firestore record."""
        doc_ref = db.collection("Articles").document(self.name)
        doc_ref.update(self.to_dict())
        print(f"🔄 Article '{self.name}' updated in Firestore.")

    def delete_from_firestore(self):
        """Deletes the article from Firestore."""
        db.collection("Articles").document(self.name).delete()
        print(f"❌ Article '{self.name}' deleted from Firestore.")

    def __str__(self):
        """String representation of the article."""
        return json.dumps(self.to_dict(), indent=2)

