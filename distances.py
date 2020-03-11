import requests, json, datetime, random
from SPARQLWrapper import SPARQLWrapper, JSON

MAX_REQUESTS = 5
uri = "https://query.wikidata.org/sparql"

def rev_lats(lats):
  tmp = lats.split(',')
  return tmp[1] + "," + tmp[0]

def get_queryString(file):
  with open(file, "r") as f:
    return f.read()

# WikiData query, only execute once
def query_cities():
  sparql = SPARQLWrapper(uri)
  query = get_queryString("query.rq")
  sparql.setQuery(query)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()
  bindings = results["results"]["bindings"]
  return bindings

def get_random_node(bindings):
  max_index = len(bindings)
  index = random.randrange(0,max_index,1)
  return bindings[index]

def node_to_point(node):
  return node["koord"]["value"][6:-1].replace(" ", ",")

def get_different_points(bindings):
  node1 = get_random_node(bindings)
  node2 = get_random_node(bindings)

  while node1["any"]["value"] == node2["any"]["value"]:
    node1 = get_random_node(bindings)
    node2 = get_random_node(bindings)
  
  point1 = node_to_point(node1)
  point2 = node_to_point(node2)

  print("point1: {}, point2: {}".format(point1, point2))

  return [point1, point2]


# Project osrm query 
# comprobar que no sean iguales

def get_distance(point1, point2):

  url = "http://router.project-osrm.org/route/v1/driving/" + point1 + ";" + point2
  print(url)
  response = requests.get(url)

  data = response.json()

  if data:
      #error control
      distance = data["routes"][0]["legs"][0]["distance"]
      duration = int(data["routes"][0]["legs"][0]["duration"])
      if distance and duration:
          print("Distantzia: " + str(distance/1000))
          print("Iraupena: " + str(datetime.timedelta(seconds=duration)))

          case = random.randrange(0,2,1)
          
          if case == 0: # 2 azpitik
            alternative1 = distance - random.randrange(int(distance*0.05), int(distance*0.2), 2)
            alternative2 = distance - random.randrange(int(distance*0.05), int(distance*0.2), 2)

          if case == 1: # 1 azpitik, 1 gainetik
            alternative1 = distance - random.randrange(int(distance*0.05), int(distance*0.2), 2)
            alternative2 = distance + random.randrange(int(distance*0.05), int(distance*0.2), 2)

          else: # 2 gainetik
            alternative1 = distance + random.randrange(int(distance*0.05), int(distance*0.2), 2)
            alternative2 = distance + random.randrange(int(distance*0.05), int(distance*0.2), 2)

          print("dist_zuzena: {}; dist_okerra1: {}; dist_okerra2:{}".format(int(distance/1000), int(alternative1/1000), int(alternative2/1000)))

          erantzuna = "https://map.project-osrm.org/?loc={}&loc={}".format(rev_lats(point1), rev_lats(point2))

          print(erantzuna)


if __name__ == "__main__":
  bindings = query_cities()
  points = get_different_points(bindings)
  get_distance(points[0], points[1])