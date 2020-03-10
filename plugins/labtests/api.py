from opal.core.api import patient_from_pk, LoginRequiredViewset
from plugins.labtests.utils import recent_observations
from opal.core.views import json_response


class RecentResultsApiView(LoginRequiredViewset):
    @patient_from_pk
    def retrieve(self, request, patient):
        recent_obs = recent_observations(patient, self.RELEVANT_TESTS)
        result = []
        for obs_name, summary in recent_obs.items():
            result.append({
                "name": obs_name,
                "date": summary["observation_datetime"],
                "result": summary["observation_value"]
            })

        return json_response(dict(results=result))