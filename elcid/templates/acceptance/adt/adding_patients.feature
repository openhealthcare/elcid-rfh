As a Doctor
I need to be able to add patients
So that I can comment on their issues

Given that I am on the Hepatology list
When I click Add Patient
When I enter a new Patient
Then that patient is added to the Hepatology list
I should be able to see their name, hospital number and date of birth

Given that a patient is on the Bacteraemia list
Given that I click on that patient and use the teams modal to add them to the Hepatology list
I should see a message in the demographics panel stating they have a positive blood culture

Given that a patient is on the Bacteraemia list and the Hepatology list
Given that I am on the Hepatology list
I should see the patient with a message stating they have an positive blood culture

Given that a patient is on the Bacteraemia list and the Hepatology list
Given that I click on that patient and use the teams modal to remove them from the Bacteraemia list
I should see a message in the demographics panel stating they have had recent positive blood culture

Given that a patient is on the Hepatology list and has recently been removed from the Bacteraemia list
Given that I am on the Hepatology list
I should see the patient with a message stating they recently have had a positive blood culture
