import logging


class MetricData(object):
    """
    Simple wrapper around the JSON object received
    from GET to metric API
    """
    def __init__(self, metric_dict):
        self.mdata = metric_dict
        if 'total' in self.mdata:
            self.num_records = int(self.mdata['total'])
        else:
            self.num_records = 0

    def get_cost(self):
        total_spend = 0
        for i in range(0, self.num_records):
            member = self.mdata["members"][i]
            value = member["values"][0]
            val = value["value"]
            logging.debug("value = %d", val)
            total_spend = total_spend + val
        return total_spend
