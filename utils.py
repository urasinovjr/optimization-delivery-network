import random
import json


def calculate_distance(point1, point2):
    x1 = point1[0]
    y1 = point1[1]
    x2 = point2[0]
    y2 = point2[1]
    dx = x2 - x1
    dy = y2 - y1
    distance = (dx * dx + dy * dy) ** 0.5
    return distance


def build_demand_density_map(orders, bounds, resolution):
    x_min = bounds["x_min"]
    x_max = bounds["x_max"]
    y_min = bounds["y_min"]
    y_max = bounds["y_max"]
    cols = (x_max - x_min) // resolution
    rows = (y_max - y_min) // resolution
    density = []
    for i in range(rows):
        row = []
        for j in range(cols):
            row.append(0)
        density.append(row)
    for order in orders:
        delivery_point = order["delivery_point"]
        weight = order["weight"]
        cell_x = int((delivery_point[0] - x_min) // resolution)
        cell_y = int((delivery_point[1] - y_min) // resolution)
        if 0 <= cell_x < cols and 0 <= cell_y < rows:
            density[cell_y][cell_x] = density[cell_y][cell_x] + weight
    max_value = 0
    for i in range(rows):
        for j in range(cols):
            if density[i][j] > max_value:
                max_value = density[i][j]
    if max_value > 0:
        for i in range(rows):
            for j in range(cols):
                density[i][j] = density[i][j] / max_value
    result = {
        "bounds": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max},
        "resolution": resolution,
        "density_matrix": density,
        "grid_shape": (rows, cols),
    }
    return result


def find_optimal_pp_locations(orders, k, iterations):
    centers = []
    for i in range(k):
        random_order = random.choice(orders)
        center = [random_order["delivery_point"][0], random_order["delivery_point"][1]]
        centers.append(center)
    for iteration in range(iterations):
        clusters = []
        for i in range(k):
            clusters.append([])
        for order in orders:
            min_distance = 999999999
            nearest_center_idx = 0
            for center_idx in range(len(centers)):
                center = centers[center_idx]
                dist = calculate_distance(order["delivery_point"], center)
                if dist < min_distance:
                    min_distance = dist
                    nearest_center_idx = center_idx
            clusters[nearest_center_idx].append(order)
        new_centers = []
        for cluster_idx in range(len(clusters)):
            cluster = clusters[cluster_idx]
            if len(cluster) > 0:
                sum_x = 0
                sum_y = 0
                for order in cluster:
                    sum_x = sum_x + order["delivery_point"][0]
                    sum_y = sum_y + order["delivery_point"][1]
                avg_x = sum_x / len(cluster)
                avg_y = sum_y / len(cluster)
                new_centers.append([avg_x, avg_y])
            else:
                new_centers.append(centers[cluster_idx])
        centers = new_centers
    result = {"locations": centers, "count": k}
    return result


def assign_orders_to_delivery_points(
    orders, existing_pp, new_locations, max_delivery_radius
):
    all_pp = []
    for pp in existing_pp:
        item = {"dp_id": pp["dp_id"], "location": pp["location"]}
        all_pp.append(item)
    for i in range(len(new_locations)):
        loc = new_locations[i]
        item = {"dp_id": "PP_NEW_" + str(i + 1), "location": loc}
        all_pp.append(item)
    assignments = []
    for order in orders:
        min_dist = 999999999
        assigned_to = None
        for pp in all_pp:
            dist = calculate_distance(order["delivery_point"], pp["location"])
            if dist < min_dist:
                min_dist = dist
                assigned_to = pp["dp_id"]
        assignment = {
            "order_id": order["order_id"],
            "assigned_to": assigned_to,
            "distance": min_dist,
        }
        assignments.append(assignment)
    dp_loads = {}
    for pp in all_pp:
        dp_loads[pp["dp_id"]] = 0
    for assignment in assignments:
        dp_id = assignment["assigned_to"]
        dp_loads[dp_id] = dp_loads[dp_id] + 1
    result = {"assignments": assignments, "dp_loads": dp_loads, "all_pp": all_pp}
    return result


def calculate_metrics(assignments, max_delivery_radius):
    total_distance = 0
    for a in assignments:
        total_distance = total_distance + a["distance"]
    avg_distance = total_distance / len(assignments)
    covered = 0
    for a in assignments:
        if a["distance"] <= max_delivery_radius:
            covered = covered + 1
    coverage = covered / len(assignments)
    dp_loads = {}
    for a in assignments:
        dp_id = a["assigned_to"]
        if dp_id not in dp_loads:
            dp_loads[dp_id] = 0
        dp_loads[dp_id] = dp_loads[dp_id] + 1
    dp_loads_values = []
    for dp_id in dp_loads:
        dp_loads_values.append(dp_loads[dp_id])
    total_load = 0
    for value in dp_loads_values:
        total_load = total_load + value
    mean_load = total_load / len(dp_loads_values)
    variance = 0
    for value in dp_loads_values:
        diff = value - mean_load
        variance = variance + diff * diff
    variance = variance / len(dp_loads_values)
    std_dev = variance**0.5
    if mean_load > 0:
        load_imbalance = std_dev / mean_load
    else:
        load_imbalance = 0
    result = {
        "avg_delivery_distance": round(avg_distance, 2),
        "coverage_efficiency": round(coverage, 3),
        "load_imbalance": round(load_imbalance, 3),
    }
    return result


def save_results(density_map, new_pp_locations, assignments, all_pp, metrics):
    new_delivery_points = []
    for i in range(len(new_pp_locations)):
        loc = new_pp_locations[i]
        item = {
            "dp_id": "PP_NEW_" + str(i + 1),
            "location": [round(loc[0], 1), round(loc[1], 1)],
        }
        new_delivery_points.append(item)
    delivery_zones = []
    for pp in all_pp:
        count = 0
        for a in assignments:
            if a["assigned_to"] == pp["dp_id"]:
                count = count + 1
        zone = {
            "dp_id": pp["dp_id"],
            "location": pp["location"],
            "estimated_orders": count,
        }
        delivery_zones.append(zone)
    result = {
        "demand_density_map": {
            "grid_bounds": density_map["bounds"],
            "resolution": density_map["resolution"],
            "density_matrix": density_map["density_matrix"],
        },
        "new_delivery_points": new_delivery_points,
        "delivery_zones": delivery_zones,
        "metrics": metrics,
    }

    f = open("output.json", "w", encoding="utf-8")
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.close()

    return result