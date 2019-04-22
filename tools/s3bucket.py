import os
import pdb
from process import processEuphebe
from difflib import SequenceMatcher
import boto3

PATH = os.path.join(os.getcwd(),'csv/Euphebe/')
s3 = boto3.resource('s3')
client= boto3.client('s3')

def match_name():
    '''
    function for matching images with menus for EUPHEBE
    :return: {menu_name:filename}
    '''
    mypath = os.path.join(os.getcwd()+'/euphebe_photos/')
    filenames = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath,f))]

    menus = processEuphebe.processMenu('./csv/Euphebe/menu0328.csv')
    items, columns = processEuphebe.processNutrition(PATH + 'total2.csv')
    mapped, not_found = processEuphebe.mapToMeal(menus, items)
    newly_mapped = processEuphebe.manual_input(menus, not_found, mapped, 'euphebe_manual_map_0330.p')

    menu_photo_map = {}

    for menu in newly_mapped:
        for item in newly_mapped[menu]:
            for filename in filenames:
                new_filename = filename.split('.')[0].lower().replace('_',' ')
                score = SequenceMatcher(None,item.name,new_filename).ratio()
                if score > 0.73:
                    # print('{}   |   {}  |   {}'.format(new_filename,item,score))
                    menu_photo_map[menu] = filename
    filetype = filename.split('.')[-1]
    return menu_photo_map, filetype

def match_name_frozen():
    mypath = os.path.join(os.getcwd()+'/frozengarden_photo/')
    filenames = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath,f))]
    print(filenames)

    from process.processFrozenGarden import process
    menus = [x.name for x in process()]

    menu_photho_map = {}
    for menu in menus:
        for filename in filenames:
            new_filename = filename.lower().replace('-',' ').replace('_',' ').replace('front','').split('.')[0]
            score = SequenceMatcher(None,menu, new_filename).ratio()
            if score > 0.7:
                print('{}   |   {}  |   {}'.format(new_filename,menu,score))
                menu_photho_map[menu] = filename
    filetype = filename.split('.')[-1]
    return menu_photho_map, filetype

def upload_image(path,menu_photo_map, filetype):
    if filetype == 'jpg':
        filetype = 'jpeg'
    extra_arg = {'ACL':'public-read','ContentType':'image/'+filetype,'ContentDisposition':'attachment'}
    for menu in menu_photo_map:
        s3.meta.client.upload_file(path+menu_photo_map[menu],BUCKET,menu, extra_arg)

def list_obj():
    response = client.list_objects(Bucket=BUCKET, EncodingType='url')
    return response

def check_obj(bucket_name,key):
    try:
        try:
            list_obj()
        except:
            pdb.set_trace()
            print('Possible error with credentials')
        s3.Object(bucket_name,key).load()
        return True
    except:
        print('Error getting s3.object.load()')
        return False

def get_url(bucket_name,key):
    if check_obj(bucket_name,key):
        return 'https://'+bucket_name+'.s3.amazonaws.com/'+key.replace(' ','+')
    else:
        return 'https://'+bucket_name+'.s3.amazonaws.com/squareLogo'

def get_image_url(menu_name):
    return get_url(BUCKET,menu_name)

def delete_all(password):
    if password == 'thaslwns1!':
        for each in list_obj()['Contents']:
            key = each['Key']
            obj = s3.Object(BUCKET,key)
            obj.delete()


BUCKET = 'minjoon-test-bucket'

if __name__ == "__main__":
    extra_arg = {'ACL':'public-read','ContentType':'image/png','ContentDisposition':'attachment'}
    s3.meta.client.upload_file('/home/min/Downloads/saana-square-white.png', BUCKET, 'squareLogo',extra_arg)
    ## EUPHEBE
    # euphebe_path = os.path.join(os.getcwd()+'/euphebe_photos/')
    # upload_image(euphebe_path,match_name())

    ## FROZEN GARDEN
    # frozen_path = os.path.join(os.getcwd()+'/frozengarden_photo/')
    # menu_photo_map, filetype = match_name_frozen()
    # upload_image(frozen_path,menu_photo_map, filetype)

    # from pprint import pprint
    # pprint(list_obj())
