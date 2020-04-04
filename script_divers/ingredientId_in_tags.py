from pymongo import MongoClient

client = MongoClient(
    host="127.0.0.1",
    port=27017,
    username="root",
    password="root",
    authSource="saana_db")

db = client.saana_db

tags = db.tags

print(tags.find())

for tag in tags.find():
    print(tag)
    for item in tag["avoid"]:
        print(item)
    for item in tag["prior"]:
        print(item)
    for item in tag["minimize"]:
        print(item)

