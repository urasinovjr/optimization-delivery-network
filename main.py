import json
from utils import (
    build_demand_density_map,
    find_optimal_pp_locations,
    assign_orders_to_delivery_points,
    calculate_metrics,
    save_results,
)


def load_config(filename):
    f = open(filename, "r", encoding="utf-8")
    config = json.load(f)
    f.close()
    return config


def main():
    config = load_config("config.json")
    print("=== Оптимизация сети пунктов выдачи ===")
    print("")
    districts = config["districts"]
    orders = config["historical_orders"]
    existing_pp = config["existing_pickup_points"]
    params = config["task_parameters"]
    print("Районов: " + str(len(districts)))
    print("Исторических заказов: " + str(len(orders)))
    print("Существующих ПВЗ: " + str(len(existing_pp)))
    print("Нужно разместить новых ПВЗ: " + str(params["new_pp_count"]))
    print("Максимальный радиус доставки: " + str(params["max_delivery_radius"]))
    print(
        "Разрешение сетки для интерполяции: " + str(params["interpolation_resolution"])
    )
    print("")
    bounds = {"x_min": 0, "x_max": 300, "y_min": 0, "y_max": 300}
    density_map = build_demand_density_map(
        orders, bounds, params["interpolation_resolution"]
    )
    print("")
    print("=== Карта плотности спроса ===")
    print(
        "Размер сетки: "
        + str(density_map["grid_shape"][0])
        + " x "
        + str(density_map["grid_shape"][1])
    )
    print("Разрешение: " + str(density_map["resolution"]) + " единиц")
    print("")
    print("Пример значений плотности (первые 3x3 ячейки):")
    for i in range(3):
        if i < len(density_map["density_matrix"]):
            row = density_map["density_matrix"][i]
            values = []
            for j in range(3):
                if j < len(row):
                    values.append(round(row[j], 3))
            print("  Строка " + str(i) + ": " + str(values))
    print("")
    print("=== Поиск оптимальных локаций для новых ПВЗ ===")
    new_locations = find_optimal_pp_locations(orders, params["new_pp_count"], 10)
    print("Найдено " + str(new_locations["count"]) + " оптимальных локаций:")
    for i in range(len(new_locations["locations"])):
        location = new_locations["locations"][i]
        x = round(location[0], 1)
        y = round(location[1], 1)
        print("  Новое ПВЗ N" + str(i + 1) + ": [" + str(x) + ", " + str(y) + "]")
    print("")
    print("=== Распределение заказов по ПВЗ ===")
    result = assign_orders_to_delivery_points(
        orders, existing_pp, new_locations["locations"], params["max_delivery_radius"]
    )
    assignments = result["assignments"]
    dp_loads = result["dp_loads"]
    all_pp = result["all_pp"]
    print("")
    print("Нагрузка на каждый ПВЗ:")
    for dp_id in dp_loads:
        load = dp_loads[dp_id]
        print("  " + dp_id + ": " + str(load) + " заказов")
    metrics = calculate_metrics(assignments, params["max_delivery_radius"])
    print("")
    print("=== Метрики эффективности ===")
    print(
        "Средняя дистанция доставки: "
        + str(metrics["avg_delivery_distance"])
        + " единиц"
    )
    coverage_percent = metrics["coverage_efficiency"] * 100
    print("Покрытие (coverage): " + str(round(coverage_percent, 1)) + "%")
    print("Баланс нагрузки (load_imbalance): " + str(metrics["load_imbalance"]))
    output = save_results(
        density_map, new_locations["locations"], assignments, all_pp, metrics
    )
    print("")
    print("=== Результаты сохранены в output.json ===")


if __name__ == "__main__":
    main()
