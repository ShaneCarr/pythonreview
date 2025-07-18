import hashlib

graphql_file_path = "FeedGroupNestedClients.graphql"

with open(graphql_file_path, "r", encoding="utf-8") as f:
    query_text = f.read()

# remove  leading and trailing white space
query_text = query_text.strip()

# {
#   "version": 1,
#   "sha256Hash": "a4b740b0697bfde02cf9fa6ba8f394b7736f8cb630ed44bf0b43885828548747"
# }
query_text = bytes(query_text, "utf-8").decode("unicode_escape")

hash_hex = hashlib.sha256(query_text.encode("utf-8")).hexdigest()

print("SHA-256 hash: " + hash_hex)