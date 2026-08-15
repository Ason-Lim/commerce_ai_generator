from app.main import app


def test_recommendations_v2_route_is_registered_once() -> None:
    routes = [
        route
        for route in app.routes
        if getattr(route, "path", None)
        == "/recommendations/v2"
        and "GET"
        in getattr(route, "methods", set())
    ]

    assert len(routes) == 1


def test_recommendations_v2_handler_contract() -> None:
    routes = [
        route
        for route in app.routes
        if getattr(route, "path", None)
        == "/recommendations/v2"
        and "GET"
        in getattr(route, "methods", set())
    ]

    assert len(routes) == 1

    route = routes[0]

    assert route.name == "recommendations_v2"
    assert route.endpoint.__name__ == "recommendations_v2"
