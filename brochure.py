import docx
import pdb

doc = docx.Document('test.docx')
for each in doc.paragraphs:
    print(each.text)

