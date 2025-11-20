from quizzy.database import get_geoip_info


def test_geoip():
    city = get_geoip_info("8.8.8.8")
    print(city)


if __name__ == "__main__":
    test_geoip()
