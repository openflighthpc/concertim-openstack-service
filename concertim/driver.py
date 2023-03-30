from concertim_service import ConcertimService
import signal

# The main entry point of the program
if __name__ == "__main__":
    service = ConcertimService()

    # Set up a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        service.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        service.start()
    except Exception as e:
        service._logger.exception("Unhandled exception occurred: %s", e)
        service.stop()
