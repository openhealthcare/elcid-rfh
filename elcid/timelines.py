from timeline.timelines import Timeline, TimelineElement
from elcid.models import MicrobiologyInput, Diagnosis


class SampleTimeline(Timeline):
    slug = "sample"

    elements = (
        TimelineElement(subrecord=MicrobiologyInput, group_by="when"),
        TimelineElement(subrecord=Diagnosis, group_by="date_of_diagnosis"),
    )
