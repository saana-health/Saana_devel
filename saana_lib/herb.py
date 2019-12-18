from .supplement import filter_opposing


def optimizeHerb(patient_id):
    '''
    wrapper function for selecting the best fitting herb according to Sunny's documentation

    Sunny's documentation:

   1.       Determine the patient “type” based on the questions.

See document here: https://docs.google.com/document/d/1ZhNfSeSe0OyxJD-Xt5Oo7NVrB31oDsbKF4r2AraysoA/edit
Pretty sure these questions/answers all have a spot on the database so basically depending on the answer to each question just tally how many they answered and select the type that is the highest from Warm vs Cold and Dry vs Moist.
A few of the questions don’t add a point but Jocelyn still recommended we have them and I may end up incorporating them later but for now you can ignore them.
2.       Exclude any that have contraindications/drug interactions or have opposing symptoms

a.       Ie if patient has weight gain don't give an herb that increases appetite

b.       Sheet with this information is here: https://docs.google.com/spreadsheets/d/1qvcdTgBerQOBZMv3Yrd0X9ozIiiKM-yoopmxIbxaWq4/edit?usp=sharing (“combined” tab)

It’s still somewhat under construction cause I need to work through and research all the drug classes/interactions but for right now you should code it so that it matches the column name exactly and then once I finish the associated drug-classes matrix I’ll change the column names accordingly.
Select herbs that have best matching “type”
Herbs should be OPPOSITE of the person’s type. Ie if the person describes themselves as being “Cool and Dry” the best herb would be one that is “Warm and Moist”
Best to match both temperature and moistness BUT if necessary matching temperature is more important. So select based on temperature first then moistness and if none match after you filter for ones with the wrong moistness then add those back in.
See sheet here: https://docs.google.com/spreadsheets/d/1gD93R9um21zSWtqxBpOghYRaA7RJClBwWiS0jpTbX-g/edit#gid=1670292674 (first “supplements” tab)
At the bottom you will see the type that the herb is. You’ll notice that one section has the numbers while the highlighted one just has the letter corresponding to the type. Use the highlighted one. Later it may become relevant to use the values (which quantify the coolness/warmness/moistness/dryness) but for right now just making it binary is fine.
Pick herb that matches the most symptoms!
The same sheet as above (step 3) is the matrix of symptoms and herbs. Again right now they are values but you can just consider them as binary (Yes it’s helpful or No it’s not)
Most herbs match multiple symptoms so you want to choose the one that matches as many of the symptoms of the client as possible.

    :param patient_id: ObjectId()
    :return: str - best fitting herb
    '''
    return filter_opposing.optimize_herb(patient_id)[0]

