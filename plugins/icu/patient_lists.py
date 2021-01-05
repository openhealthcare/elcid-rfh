"""
Patient lists for our ICU plugin
"""
from opal.core.patient_lists import PatientList
from opal.models import Episode, Patient

from elcid.episode_categories import InfectionService
from elcid.patient_lists import RfhPatientList



# class AutoICUSouthList(RfhPatientList, PatientList):
#     is_read_only  = True
#     schema        = []
#     template_name = 'episode_list.html'
#     display_name  = 'Auto ICU South'
#     order         = 30

#     @property
#     def queryset(self):
#         patients = Patient.objects.filter(icuhandoverlocation__ward='South')
#         return Episode.objects.filter(
#             patient__in=patients,
#             category_name=InfectionService.display_name
#         ).distinct()

#     @classmethod
#     def visible_to(klass, user):
#         return True


# class AutoICUEastList(RfhPatientList, PatientList):
#     is_read_only  = True
#     schema        = []
#     template_name = 'episode_list.html'
#     display_name  = 'Auto ICU East'
#     order         = 30

#     @property
#     def queryset(self):
#         patients = Patient.objects.filter(icuhandoverlocation__ward='East')
#         return Episode.objects.filter(
#             patient__in=patients,
#             category_name=InfectionService.display_name
#         ).distinct()

#     @classmethod
#     def visible_to(klass, user):
#         return True


# class AutoICUWestList(RfhPatientList, PatientList):
#     is_read_only  = True
#     schema        = []
#     template_name = 'episode_list.html'
#     display_name  = 'Auto ICU West'
#     order         = 30

#     @property
#     def queryset(self):
#         patients = Patient.objects.filter(icuhandoverlocation__ward='West')
#         return Episode.objects.filter(
#             patient__in=patients,
#             category_name=InfectionService.display_name
#         ).distinct()

#     @classmethod
#     def visible_to(klass, user):
#         return True


# class AutoICU3NorthAList(RfhPatientList, PatientList):
#     is_read_only  = True
#     schema        = []
#     template_name = 'episode_list.html'
#     display_name  = 'Auto ICU 3 North A'
#     order         = 30

#     @property
#     def queryset(self):
#         patients = Patient.objects.filter(icuhandoverlocation__ward='3NorthA')
#         return Episode.objects.filter(
#             patient__in=patients,
#             category_name=InfectionService.display_name
#         ).distinct()

#     @classmethod
#     def visible_to(klass, user):
#         return True



# class AutoICU2List(RfhPatientList, PatientList):
#     is_read_only  = True
#     schema        = []
#     template_name = 'episode_list.html'
#     display_name  = 'Auto ICU 2'
#     order         = 31

#     @property
#     def queryset(self):
#         patients = Patient.objects.filter(icuhandoverlocation__ward='ICU2')
#         return Episode.objects.filter(
#             patient__in=patients,
#             category_name=InfectionService.display_name
#         ).distinct()

#     @classmethod
#     def visible_to(klass, user):
#         return True
