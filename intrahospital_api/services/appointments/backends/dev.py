import datetime
import random
import copy
from intrahospital_api.services.appointments.backends import live

TEST_DATA = {
    u'AIG_Resource_ID': u'RAL Davis, Dr David TB',
    u'AIL_Location_Resource_ID': u'RAL GROVE CLINIC^^^RAL RF^^AMB^RFH',
    u'AIP_Personnel_ID': u'',
    u'Appointment_Duration': u'10',
    u'Appointment_Duration_Units': u'MINUTES',
    u'Appointment_End_Datetime': datetime.datetime(2018, 9, 18, 14, 10),
    u'Appointment_ID': u'43062932.000',
    u'Appointment_Start_Datetime': datetime.datetime(2018, 9, 18, 14, 0),
    u'Appointment_Status_Code': u'Confirmed',
    u'Derived_Appointment_Location': u'RAL GROVE CLINIC',
    u'Derived_Appointment_Location_Site': u'RAL RF',
    u'Derived_Appointment_Type': u'Thoracic TB F/Up',
    u'Encounter_Number': u'6750589',
    u'Filler_Appointment_ID': u'',
    u'Full_Appointment_Type': u'Thoracic TB F/Up^^^Thoracic TB F/Up',
    u'HL7_Message_Date': datetime.datetime(2018, 8, 14, 14, 53, 18),
    u'HL7_Message_ID': u'Q526242548T581575044',
    u'HL7_Message_Type': u'SIU^S12',
    u'Hospital_Service': u'360',
    u'Patient_Number': u'111111',
    u'TCI_DateTime': None,
    u'TCI_DateTime_Text': u'',
    u'TCI_Location': u'',
    u'Visit_ID': u'12331095',
    u'derived_clinic_resource': u'RAL Davis, Dr David TB',
    u'id': 8510106,
    u'insert_date': datetime.datetime(2018, 8, 14, 14, 56, 12, 947000),
    u'last_updated': None,
    u'vAccount_Status': u'PREADMIT',
    u'vAttending_Doctor_Code': u'C3251380',
    u'vAttending_Doctor_Name': u'Davis, David',
    u'vPatient_Class': u'PREADMIT',
    u'vPatient_Forename': u'Wilma',
    u'vPatient_Surname': u'Flintstone',
    u'vPatient_DOB': datetime.datetime(1981, 1, 7, 0, 0),
    u'vPatient_Number': u'111111',
    u'vPatient_Type': u'PREADMIT',
    u'vReferring_Doctor_Code': u'~',
    u'vReferring_Doctor_Name': u''
}


class Api(live.Api):
    def __init__(self):
        pass

    def raw_appointment(self, hospital_number):
        test_data = copy.copy(TEST_DATA)
        test_data["Patient_Number"] = hospital_number
        test_data["insert_date"] = datetime.datetime.now()
        time_jump = datetime.timedelta(
            random.randint(1, 10)
        )
        start = datetime.datetime.now() + time_jump
        end = start + datetime.timedelta(hours=1)
        test_data["Appointment_Start_Datetime"] = start
        test_data["Appointment_End_Datetime"] = end
        return test_data

    def raw_appointments(self, hospital_number):
        return [self.raw_appointment(hospital_number)]

    def raw_appointments_for_hospital_number(self, hospital_number):
        return self.raw_appointments(hospital_number)

    def raw_tb_appointments_for_hospital_number(self, hospital_number):
        return self.raw_appointments(hospital_number)
