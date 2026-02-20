from fastapi import FastAPI,Path,HTTPException,Query
from pydantic import BaseModel,Field,computed_field
from fastapi.responses import JSONResponse
from typing import Annotated,Literal,Optional
import json 

app = FastAPI()

class Patient_Create(BaseModel):
  
  patient_id : Annotated[str , Field(..., description='patient id from database',examples=['P001'])]
  gender : Annotated[Literal['male','female','others'],Field(..., description='gender can be male or female ')]
  height : Annotated[float , Field(..., gt=0, description='The Height in Cm')]
  weight : Annotated[float , Field(..., gt=0, description='Weight in Kg')]

  @computed_field
  @property
  def bmi(self)->float:
    bmi = round((self.weight / self.height**2),2)
    return (bmi)

  @computed_field
  @property
  def verdict(self)->str:
    if self.bmi < 18.5:
      return ('Underweight')
    elif self.bmi < 25:
      return ('Normal')
    elif self.bmi < 30:
      return ('Normal')
    else:
      return ('Obese')
class Patient_Update(BaseModel):

    gender: Optional[Literal['male','female','others']] = None
    height: Optional[float] = Field(gt=0, description="The Height in Cm",default=None)
    weight: Optional[float] = Field(gt=0, description="Weight in Kg",default=None)

@app.get('/')
def home():
  return {'message':'Patient Management System'}

@app.get('/about')
def about():
  return {'message':'API for Patient Management'}

def get_data():
  with open ('patient.json','r') as f:
    data = json.load(f)
    return (data)

def save_data(data):
  with open ('patient.json','w') as f:
    json.dump(data , f)

@app.get('/view')
def view_all_patients():
  # load the data
  data = get_data()
  return (data)

@app.get('/patient/{patient_id}')
def single_patient(patient_id :str = Path(..., description='patient id from database',example='P001')):
  # load data 
  data = get_data()

  for patient in data:
    if patient['patient_id'] == patient_id:
      return patient
  raise HTTPException(status_code=400 , detail='Invalid Patient Id And Patient Not Found')

@app.get('/sort')
def sorting_of_patients(sort_by : str = Query(..., description='sort on the basis of height , weight or bmi'), order : str = Query('asc',description='patients can be sort in ascending and descending order only')):

  valid_sorting_fields = ['height','weight','bmi']
  valid_ordering_fields = ['asc','desc']

  if sort_by not in valid_sorting_fields:
    raise HTTPException(status_code=400 , detail=f'invalid field name choose from {valid_sorting_fields}')
  
  if order not in valid_ordering_fields:
    raise HTTPException(status_code=400 , detail=f'invalid order choose from {valid_ordering_fields}')
  
  # load the data 
  data = get_data()

  sorted_data = sorted(data, key=lambda x:x.get(sort_by,0),reverse=True if order=='desc' else False)

  return (sorted_data)
  
@app.post('/create')
def create_patient(patient :Patient_Create):

  # Step 1 . Load The Existing Data
  data = get_data()

  # Step 2. If Patient Already Exists
  for p in data:
    if p['patient_id'] == patient.patient_id:
      raise HTTPException (
          status_code=400 ,
          detail='Patient Already Exist'
      )
  # Step 3. Add the Patient to db 
  data.append(patient.model_dump()) # save in memory to save permanently in file create save data fun to save it
  save_data(data)
  # Step 4. Return Json Response
  return JSONResponse(
    status_code=401,
    content='Patient Created SucessFully'
  )

@app.put('/update/{patient_id}')
def update_patient(
    updated_data: Patient_Update, 
    patient_id: str = Path(..., description='Patient Id For updating', example='P001')
):

    data = get_data()
    for p in data:
        if p['patient_id'] == patient_id:

            updated_dict = updated_data.model_dump(exclude_unset=True)

            # for key, value in updated_dict.items():
            #     p[key] = value

            p.update(updated_dict)

            save_data(data)

            return {"message": "Patient Updated Successfully"}

    raise HTTPException(status_code=404, detail="Patient Not Found")

@app.delete('/delete/{patient_id}')
def delete_patient(
    patient_id: str = Path(..., description='Patient Id Required For deleting Patient', example='P001')
):
    data = get_data()
    for index, patient in enumerate(data):
        if patient['patient_id'] == patient_id:
            deleted_patient = data.pop(index)  # remove correctly
            save_data(data)
            return JSONResponse(
                status_code=200,
                content=f"Patient {deleted_patient['patient_id']} Deleted Successfully"
            )
    # if not found
    raise HTTPException(
        status_code=404,
        detail="Patient Not Found"
    )