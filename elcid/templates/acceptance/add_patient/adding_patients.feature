As a Doctor
I need to be able to add patients
So that I can comment on their issues

Given that I am on a patient list
When I click Add Patient in the nav bar
I should be able taken to a new page to add a patient

Given that I am on the add patient page
Given that I insert the hospital number of a patient that exists in elcid
I should be shown their demographics
When I click next, I should be taken through to a Location form.
When I add the location and team and press save, I should be redirected
patient detail screen with a new episode with that location.


Given that I am on the add patient page
Given that I insert the hospital number of a patient that doesn't exist (prefixed with x if running locally).
I should have the option to add in demographics
When I click next, I should be taken through to a Location form.
When I add the location and team and press save, I should be redirected
patient detail screen with a new episode with that location.

Given that I am on the add patient page
Given that I insert the hospital number of a patient that exists but not in elcid.
I should be shown their demographics.
when I click next, I should be taken through to a Location form.
When I add the location and team and press save, I should be redirected
patient detail screen with a new episode with that location.
