
from capability_detector import RouterCapabilityDetector


def main():
    gateway = "192.168.100.1"

    detector = RouterCapabilityDetector(gateway)
    detector.mostrar()


if __name__ == "__main__":
    main()
