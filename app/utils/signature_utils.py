from pymongo import MongoClient

# Initialize MongoDB client
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']

def get_document_base64(document_id):
    # Find the document in the watchers collection
    document = db.documents.find_one({"document_id": document_id})
    if document and "document_base64" in document:
        return document["document_base64"]
    return None

def get_signature_base64(signer_id, document_id):
    # Find the signer document in the signerdocuments collection
    signer_document = db.signerdocuments.find_one({"signer_id": signer_id, "document_id": document_id})
    if signer_document and "signature" in signer_document:
        return signer_document["signature"]
    return None

# def get_coordinates(signer_id, document_id):
#     # Find the document in the documents collection
#     document = db.documents.find_one({"document_id": document_id})

#     if document and "signers" in document:
#         signers = document["signers"]
#         for signer in signers:
#             if signer.get("signer_id") == signer_id:
#                 if "coordinates" in signer:
#                     return signer["coordinates"]
#                 else:
#                     return None

#     return None

def get_coordinates(signer_id, document_id):
    # Find the document in the documents collection
    document = db.documents.find_one({"document_id": document_id})

    if document and "signers" in document:
        signers = document["signers"]
        for signer in signers:
            if signer.get("signer_id") == signer_id:
                if "coordinates" in document:
                    # Find the signer's order
                    signer_order = signer.get("order")
                    if signer_order is not None:
                        # Use signer_order-1 to get the correct index (0-based index)
                        if signer_order <= len(document["coordinates"]):
                            coordinates = document["coordinates"][signer_order - 1]
                            return coordinates
                        else:
                            print(f"Signer {signer_id} has no assigned coordinates")
                            return None
                    else:
                        print(f"Order not specified for signer {signer_id}")
                        return None
                else:
                    print(f"No coordinates found in the document {document_id}")
                    return None
        print(f"Signer with signer_id {signer_id} not found in document {document_id}")
    else:
        print(f"Document {document_id} not found in the database")

    return None


