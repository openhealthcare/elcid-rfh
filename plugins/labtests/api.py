from opal.core.api import patient_from_pk, LoginRequiredViewset
from plugins.labtests.utils import recent_observations
from opal.core.views import json_response


class RecentResultsApiView():
    @patient_from_pk
    def retrieve(self, request, patient):
        recent_obs = recent_observations(self.RELEVANT_TESTS)
        result = []
        for obs_name, summary in tb_summary_information.items():
            result.append({
                "name": obs_name,
                "date": summary["observation_datetime"],
                "result": summary["observation_value"]
            })

        return json_response(dict(results=result))