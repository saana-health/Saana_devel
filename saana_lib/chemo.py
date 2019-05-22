from . import connectMongo
import pdb

def get_chemo_dates(patient_id, date_from, date_to):
    chemo_dates = list(connectMongo.db.patient_treatment_dates.find({'patient_id':patient_id, 'treatment_date':\
        {'$gte':date_from, '$lte':date_to}}))
    treatment_dates = [x['treatment_date'] for x in chemo_dates]
    delta_dates = [(treatment_date - date_from).days for treatment_date in treatment_dates]
    return delta_dates

def choose_chemo_meals(score_board,slots, supplierIds):
    # first look at current meals and choose more from the score_board
    chemo_meals = []
    for meal in slots:
        if 'soup' in meal['meal'].type:
            chemo_meals.append(meal['meal'])

    if len(chemo_meals) >= 3:
        return chemo_meals

    for score in score_board:
        meals = score_board[score]
        if len(chemo_meals) >= 3:
            return chemo_meals
        for meal in meals:
            # SKIP if not one of the suppliers we already chose
            if meal['meal'].supplier_id not in supplierIds:
                continue
            if 'soup' in meal['meal'].type:
                chemo_meals.append(meal['meal'])
    return chemo_meals


def reorder_chemo(slots, patient_id, start_date, end_date, score_board, supplierIds):
    delta_dates = get_chemo_dates(patient_id, start_date, end_date)
    if delta_dates == []:
        return slots
    else:
        chemo_meals = choose_chemo_meals(score_board, slots, supplierIds)
        pdb.set_trace()
        return slots

