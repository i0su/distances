import requests, json, datetime, random, time, csv, os, uuid
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

  while node1["any"]["value"] == node2["any"]["value"] or not is_valid_node(node1) or not is_valid_node(node2):
    node1 = get_random_node(bindings)
    node2 = get_random_node(bindings)
  
  point1 = node_to_point(node1)
  point2 = node_to_point(node2)
  label1 = get_label(node1)
  label2 = get_label(node2)

  print("point1: {}, point2: {}".format(point1, point2))

  return (label1, point1), (label2, point2)

def is_valid_node(node):
  return node["anyLabel"]["value"][0] != "Q"

def get_label(node):
  return node["anyLabel"]["value"]

def draw_map(point1, point2):
  url_template = "http://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
  map_height = 600
  map_width = 600
  fName = str(uuid.uuid4().hex)

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

  image.save("./maps/" + fName + ".png")
  print("map created")

  return fName

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

def wrong_distances(distance):
  min_proportion = 0.1
  max_proportion = 0.2

  case = random.randrange(0,3)
  if case == 0: # 2 azpitik
    alternative1 = distance - random.randrange(int(distance*min_proportion), int(distance*max_proportion), 2)
    alternative2 = distance - random.randrange(int(distance*min_proportion), int(distance*max_proportion), 2)

  if case == 1: # 1 azpitik, 1 gainetik
    alternative1 = distance - random.randrange(int(distance*min_proportion), int(distance*max_proportion), 2)
    alternative2 = distance + random.randrange(int(distance*min_proportion), int(distance*max_proportion), 2)

  else: # 2 gainetik
    alternative1 = distance + random.randrange(int(distance*min_proportion), int(distance*max_proportion), 2)
    alternative2 = distance + random.randrange(int(distance*min_proportion), int(distance*max_proportion), 2)

  return alternative1, alternative2


def format_distance(distance):
  return int(distance/1000)


# Project osrm query 

def get_distance(location1, location2):
  distance, duration = osrm_query(location1[1], location2[1])

  if distance and duration:
    #print("Iraupena: " + str(datetime.timedelta(seconds=duration)))

    alternative1, alternative2 = wrong_distances(distance)

    distance = format_distance(distance)
    alternative1 = format_distance(alternative1)
    alternative2 = format_distance(alternative2)

    print("Zer distantzia dago {} eta {}ren artean?".format(location1[0], location2[0]))
    print("dist_zuzena: {}; dist_okerra1: {}; dist_okerra2:{}".format(distance, alternative1, alternative2))

    while distance == alternative1 or distance == alternative2 or alternative1 == alternative2:
      alternative1, alternative2 = wrong_distances(distance)

    erantzuna = "https://www.openstreetmap.org/directions?route={}%3B{}".format(rev_lats(location1[1]), rev_lats(location2[1]))
    print(erantzuna)

    return distance, alternative1, alternative2, erantzuna

def write_response(label1, label2, img_path, correct, incorrect1, incorrect2, url, file_path):
  with open (file_path, "a") as file:
    fieldnames = ['Mota', 'Galdera', 'Irudia', 'Zuzena', 'Oker1', 'Oker2', 'Jatorria', 'Esteka']
    response_writer = csv.writer(file, delimiter=";", lineterminator=";;\n")
    if os.stat(file_path).st_size == 0:
      response_writer.writerow(fieldnames)
    question = "Zer distantzia dago {} eta {}ren artean?".format(label1, label2)
    line = ["Distantziak", question, img_path, correct, incorrect1, incorrect2, "OpenStreetMap", url]
    response_writer.writerow(line)


if __name__ == "__main__":
  bindings = query_cities()
  location1, location2 = get_different_points(bindings)
  distance, alternative1, alternative2, url = get_distance(location1, location2)
  fname = draw_map(location1[1], location2[1])
  write_response(location1[0], location2[0], fname, distance, alternative1, alternative2, url, "distances.csv")
