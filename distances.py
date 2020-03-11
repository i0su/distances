import requests, json, datetime, random, time
from SPARQLWrapper import SPARQLWrapper, JSON
from staticmap import StaticMap, Line, CircleMarker, IconMarker
from PIL import Image, ImageDraw, ImageFont

MAX_REQUESTS = 20

def rev_lats(lats):
  tmp = lats.split(',')
  return tmp[1] + "," + tmp[0]

def point_to_coordinates(point):
  parts = point.split(",")
  return tuple([float(x) for x in parts])

def get_queryString(file):
  with open(file, "r") as f:
    return f.read()

def generate_label(text):
  path = "./labels"
  font_path = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'

  img = Image.new('RGBA', (800, 100))
  fnt = ImageFont.truetype(font_path, 35)
  d = ImageDraw.Draw(img)
  d.text((0,0), text, fill=(0,0,0), font=fnt)
  
  fname = text.replace(" ", "_")
  full_path = path + fname + ".png"

  img.save(full_path)

  return full_path


# WikiData query, only execute once
def query_cities():
  uri = "https://query.wikidata.org/sparql"
  query_path = "query.rq"
  
  query = get_queryString(query_path)

  sparql = SPARQLWrapper(uri)
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


def draw_map(point1, point2, file_path):
  url_template = "http://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
  map_height = 500
  map_width = 500

  m = StaticMap(map_height, map_width, url_template=url_template)

  coords1 = point_to_coordinates(point1)
  coords2 = point_to_coordinates(point2)

  marker_outline1 = CircleMarker(coords1, 'white', 18)
  marker1 = CircleMarker(coords1, '#0036FF', 12)
  m.add_marker(marker_outline1)
  m.add_marker(marker1)

  marker_outline2 = CircleMarker(coords2, 'white', 18)
  marker2 = CircleMarker(coords2, '#0036FF', 12)
  m.add_marker(marker_outline2)
  m.add_marker(marker2)

  image = m.render(zoom=9)

  image.save(file_path)
  print("map created")


def osrm_query(point1, point2):
  url = "http://router.project-osrm.org/route/v1/driving/" + point1 + ";" + point2
  print(url)

  response = requests.get(url)
  data = response.json()

  if data:
    i=1
    completed = False
    while not completed:
      try:
        distance = data["routes"][0]["legs"][0]["distance"]
        duration = int(data["routes"][0]["legs"][0]["duration"])
        completed = True
      except:
        response = requests.get(url)
        data = response.json()
        print("Attempting to request router.project-osrm.org...")
        print("Number of attempts: {}".format(i))
      i+=1
      time.sleep(2)

    return distance, duration


# Project osrm query 
# comprobar que no sean iguales

def get_distance(point1, point2):
  distance, duration = osrm_query(point1, point2)

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

    #cambiar  a url de osm
    erantzuna = "https://map.project-osrm.org/?loc={}&loc={}".format(rev_lats(point1), rev_lats(point2))

    print(erantzuna)


if __name__ == "__main__":
  bindings = query_cities()
  points = get_different_points(bindings)
  get_distance(points[0], points[1])
  draw_map(points[0], points[1], "test.png")