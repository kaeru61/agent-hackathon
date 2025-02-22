import pcse, os
import pandas as pd
from pcse.models import Wofost71_PP
from pcse.fileinput import YAMLAgroManagementReader, YAMLCropDataProvider, CABOFileReader
from pcse.base import ParameterProvider
from pcse.input import NASAPowerWeatherDataProvider

class CropSimulation:
    crops = ['wheat', 'maize', 'barley', 'sorghum', 'soybean', 'rice', 'millet', 'sunflower', 'potato']
    crop_varieties = {
        'wheat': ['Aragorn', 'Soissons', 'Apache', 'Caphorn', 'Cordiale'],
        'maize': ['Pioneer', 'DKC', 'Agrimax', 'KWS', 'LG'],
        'barley': ['Sebastian', 'Igri', 'KWS', 'Quench', 'Talisman'],
        'sorghum': ['Pioneer', 'NK', 'Agrimax', 'KWS', 'LG'],
        'soybean': ['Pioneer', 'NK', 'Agrimax', 'KWS', 'LG'],
        'rice': ['Rice_501', 'NK', 'Agrimax', 'KWS', 'LG'],
        'millet': ['Pioneer', 'NK', 'Agrimax', 'KWS', 'LG'],
        'sunflower': ['Pioneer', 'NK', 'Agrimax', 'KWS', 'LG'],
        'potato': ['Pioneer', 'NK', 'Agrimax', 'KWS', 'LG']
    }

    def __init__(self, crop_name, crop_variety, coordinates, soil_filename):
        self.crop_name = crop_name
        self.crop_variety = crop_variety
        self.soil_filename = soil_filename
        self.longitude = coordinates[0]
        self.latitude = coordinates[1]

    def run_simulation(self):
        # 作物データの読み込み
        cropdata = YAMLCropDataProvider(force_reload=True)
        if self.crop_name not in self.crops:
          raise ValueError(f"Invalid crop name: {self.crop_name}")
        if self.crop_variety not in self.crop_varieties[self.crop_name]:
          raise ValueError(f"Invalid crop variety: {self.crop_variety}")

        cropdata.set_active_crop(self.crop_name, self.crop_variety)

        # 土壌データの読み込み
        soildata = CABOFileReader(os.getcwd()+"/src/functions/data/"+self.soil_filename)

        # 農業管理データの読み込み
        agromanagement = YAMLAgroManagementReader(os.getcwd()+"/src/functions/data/"+self.crop_name+".agro")

        # 気象データの読み込み
        wdp = NASAPowerWeatherDataProvider(latitude=self.latitude, longitude=self.longitude)


        # モデルの初期化
        wdfost = Wofost71_PP(ParameterProvider(cropdata=cropdata, soildata=soildata), wdp, agromanagement)

        # シミュレーションの実行
        wdfost.run_till_terminate()

        # 結果の取得
        df = pd.DataFrame(wdfost.get_output())
        return df


# Example usage
if __name__ == "__main__":
    coordinates = [140.3819, 36.377]
    simulation = CropSimulation("rice", "Rice_501", coordinates, "ec3.soil")
    df = simulation.run_simulation()
    print(df.tail())
