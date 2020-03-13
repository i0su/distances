import requests, random, time, csv, os, uuid
from SPARQLWrapper import SPARQLWrapper, JSON
from staticmap import StaticMap, Line, CircleMarker, IconMarker
from PIL import Image, ImageDraw, ImageFont

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

  #print("point1: {}, point2: {}".format(point1, point2))

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

  image = m.render(zoom=8)

  image.save("./maps/" + fName + ".png")
  #print("map created")

  return fName+".png"

def osrm_query(point1, point2):
  url = "http://router.project-osrm.org/route/v1/driving/" + point1 + ";" + point2
  #print(url)

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
        #print("Attempting to request router.project-osrm.org...")
        #print("Number of attempts: {}".format(i))
      i+=1
      time.sleep(2)

    return distance, duration

def wrong_answers(answer):
  min_proportion = 0.1
  max_proportion = 0.3

  case = random.randrange(0,3)
  if case == 0: # 2 azpitik
    alternative1 = answer - random.randrange(int(answer*min_proportion), int(answer*max_proportion), 2)
    alternative2 = answer - random.randrange(int(answer*min_proportion), int(answer*max_proportion), 2)

  if case == 1: # 1 azpitik, 1 gainetik
    alternative1 = answer - random.randrange(int(answer*min_proportion), int(answer*max_proportion), 2)
    alternative2 = answer + random.randrange(int(answer*min_proportion), int(answer*max_proportion), 2)

  else: # 2 gainetik
    alternative1 = answer + random.randrange(int(answer*min_proportion), int(answer*max_proportion), 2)
    alternative2 = answer + random.randrange(int(answer*min_proportion), int(answer*max_proportion), 2)

  return alternative1, alternative2


def format_distance(distance):
  return int(distance/1000)

def format_duration(minutes):
  hours, minutes = divmod(minutes, 60)
  if hours:
    return  "{} ordu eta {} minutu".format(hours, minutes)
  else:
    return "{} minutu".format(minutes)

    
# Divide into 2 functions?

def get_distance(location1, location2):
  distance, duration = osrm_query(location1[1], location2[1])

  if distance and duration:

    # Get two alternative distances
    alternative_distance1, alternative_distance2 = wrong_answers(distance)

    distance = format_distance(distance)
    alternative_distance1 = format_distance(alternative_distance1)
    alternative_distance2 = format_distance(alternative_distance2)

    #print("Zer distantzia dago {} eta {}ren artean?".format(location1[0], location2[0]))
    #print("dist_zuzena: {}; dist_okerra1: {}; dist_okerra2:{}".format(distance, alternative_distance1, alternative_distance2))

    #into a function?
    while distance == alternative_distance1 or distance == alternative_distance2 or alternative_distance1 == alternative_distance2:
      alternative_distance1, alternative_distance2 = wrong_answers(distance)

    # Get two alternative durations
    duration = int(duration/60)
    alternative_duration1, alternative_duration2 = wrong_answers(duration)

    while duration == alternative_duration1 or distance == alternative_duration2 or alternative_duration1 == alternative_duration2:
      alternative_duration1, alternative_duration2 = wrong_answers(duration)

    duration = format_duration(duration)
    alternative_duration1 = format_duration(alternative_duration1)
    alternative_duration2 = format_duration(alternative_duration2)

    #print("Zenbat denbora dago kotxez {} eta {}ren artean?".format(location1[0], location2[0]))
    #print("dist_zuzena: {}; dist_okerra1: {}; dist_okerra2:{}".format(duration, alternative_duration1, alternative_duration2))

    erantzuna = "https://www.openstreetmap.org/directions?route={}%3B{}".format(rev_lats(location1[1]), rev_lats(location2[1]))
    #print(erantzuna)

    return distance, alternative_distance1, alternative_distance2, duration, alternative_duration1, alternative_duration2, erantzuna

def write_response(question_type, label1, label2, img_path, correct, incorrect1, incorrect2, url, file_path):
  distance_question = "Zer distantzia dago {} eta {}ren artean?"
  duration_question = "Zenbat denbora behar da {}tik {}ra kotxez joateko?"
  source = "OpenStreetMap"
  distance_type = "Distantziak"
  duration_type = "Iraupenak"

  with open (file_path, "a") as file:
    fieldnames = ['Mota', 'Galdera', 'Irudia', 'Zuzena', 'Oker1', 'Oker2', 'Jatorria', 'Esteka']
    response_writer = csv.writer(file, delimiter=";", lineterminator=";;\n")

    if os.stat(file_path).st_size == 0:
      response_writer.writerow(fieldnames)

    if question_type == "d":
      question = distance_question.format(label1, label2)
      actual_type = distance_type 
    if question_type == "t":
      question = duration_question.format(label1, label2)
      actual_type = duration_type

    row = [actual_type, question, img_path, correct, incorrect1, incorrect2, source, url]
    response_writer.writerow(row)

def generate_n_questions(n):
  distances_file = "distances.csv"
  durations_file = "durations.csv"

  start_time = time.time()
  print("Hasiera. {} galdera sortzen...\n".format(n))
  bindings = query_cities()

  if bindings:
    print("Hiri eta herrien querya egin da.\n")

    for i in range(1,n+1):
      location1, location2 = get_different_points(bindings)
      distance, alternative_distance1, alternative_distance2, duration, alternative_duration1, alternative_duration2, url = get_distance(location1, location2)
      fname = draw_map(location1[1], location2[1])
      write_response("d", location1[0], location2[0], fname, distance, alternative_distance1, alternative_distance2, url, distances_file)
      write_response("t", location1[0], location2[0], fname, duration, alternative_duration1, alternative_duration2, url, durations_file)
      print("Galdera zuzen sortu da.")
      print("Orain arte sortutako galdera kopurua: {} \n".format(i))

  else:
    print("Errorea wikidata zerbitzariarekin konektazerakoan.")

  exec_time = time.time() - start_time
  m, s = divmod(exec_time, 60)
  h, m = divmod(m, 60)  

  print("Galderen sorrera amaitu da.")

  return "{}:{}:{}".format(int(h), int(m), int(s))
  
if __name__ == "__main__":
  NUM_QUESTIONS = 5
  exec_time = generate_n_questions(NUM_QUESTIONS)
  print("Exekuzio denbora {} galdera sortzeko: {}".format(NUM_QUESTIONS, exec_time))