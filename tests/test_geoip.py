from quizzy.database import get_geoip_info


def test_geoip():
    city = get_geoip_info("8.8.8.8")
    print(city.city)
    print(city.location.latitude)
    print(city.location.longitude)
    print(city.location.accuracy_radius)
    print(city.postal)


if __name__ == "__main__":
    test_geoip()
