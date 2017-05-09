from urllib import request,parse
from xml.parsers.expat import ParserCreate

def fetch_xml(url):
    with request.urlopen(url) as f:
        data=f.read()
        return data.decode('utf-8')

class WeatherSaxHandler():
    def __init__ (self):
        self.weather_data={}
        self.date_index=0

    def start_element(self,name,attrs):
        if name=='yweather:location':
            self.weather_data['city']=attrs['city']
            self.weather_data['country']=attrs['country']
        if name=='yweather:forecast' and self.date_index<2:
            if self.date_index==0:
                self.weather_data['today'] = {}
                self.weather_data['today']['text'] = attrs['text']
                self.weather_data['today']['low'] = int(attrs['low'])
                self.weather_data['today']['high'] = int(attrs['high'])
                self.date_index += 1
            elif self.date_index==1:
                self.weather_data['tomorrow'] = {}
                self.weather_data['tomorrow']['text'] = attrs['text']
                self.weather_data['tomorrow']['low'] = int(attrs['low'])
                self.weather_data['tomorrow']['high'] = int(attrs['high'])
                self.date_index += 1
    def end_element(self,name):
        pass

    def char_data(self,text):
        pass

def parse_weather(xml):
    handler=WeatherSaxHandler()
    parse=ParserCreate()
    parse.StartElementHandler=handler.start_element
    parse.EndElementHandler=handler.end_element
    parse.CharacterDataHandler=handler.char_data
    parse.Parse(xml)
    return handler.weather_data

d='https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20weather.forecast%20where%20woeid%20in%20(select%20woeid%20from%20geo.places(1)%20where%20text%3D%22beijing%2C%20china%22)%20and%20u%3D%27c%27%20&format=xml&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeysw%2C%20scotland%22)%20and%20u%3D%27c%27%20&format=xml&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys'

weather = parse_weather(fetch_xml(d))

print('Weather:', str(weather))