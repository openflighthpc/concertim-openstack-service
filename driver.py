from openstack.service import OpenstackService
from concertim.service import ConcertimService
from data_handler.handler import DataHandler

import signal

# The main entry point of the program
if __name__ == "__main__":
    openstack = OpenstackService()
    concertim = ConcertimService()
    handler = DataHandler(openstack,concertim)

    # Set up a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        handler.stop()
        openstack.disconnect()
        concertim.disconnect()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        handler.start()
    except Exception as e:
        handler.logger.exception("Unhandled exception occurred: %s", e)
        handler.stop()
        openstack.disconnect()
        concertim.disconnect()
