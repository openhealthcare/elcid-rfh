### Add Patients

#### There are 3 stages.
Stage 1 /add-patients/gather-hospital-numbers:
A big text box, paste in your numbers, we split them by spaces/commas/new lines.
Query all of them and stick the result in a session variable of
{hn: FOUND IN ELCID}

Stage 2 /add-patients/lookup-numbers:
a static page with a controller that we pass our session variable as json
display it on the page, for anything we don't have we query with the search item
there is also an edit button which retriggers the search functionality.
Post this form for Stage 3

Stage 3 POST these back in a hidden input


