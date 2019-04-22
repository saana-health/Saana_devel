from process import processEuphebe
import connectMongo

print('Adding Euphebe meals')
combined = processEuphebe.process(PATH, 'menu0328.csv', 'total2.csv')
connectMongo.insert_meal(combined)
print('Done')