import pcse, os
import pandas as pd
from pcse.models import Wofost71_PP
from pcse.fileinput import YAMLAgroManagementReader, YAMLCropDataProvider, CABOFileReader
from pcse.base import ParameterProvider
from pcse.input import NASAPowerWeatherDataProvider

class CropSimulation:
    crops = ['wheat', 'rice', 'potato']
    crop_varieties = {
        'wheat': ['Winter_wheat_101', 'Winter_wheat_102', 'Winter_wheat_103', 'Winter_wheat_104', 'Winter_wheat_105', 'Winter_wheat_106', 'Winter_wheat_107', 'bermude', 'apache'],
        'rice': ['Rice_501', 'Rice_HYV_IR8', 'Rice_IR64616H_DS', 'Rice_IR64616H_WS', 'Rice_IR64', 'Rice_IR72', 'Rice_IR72_DS', 'Rice_IR72_WS', 'Rice_IR8A'],
        'potato': ['Potato_701', 'Potato_702', 'Potato_703', 'Potato_704', 'Innovator', 'Fontane', 'Markies', 'Premiere', 'Festien']
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

def run_simulation(crop_name: str, lat: float, lon: float) -> float:
    """シミュレーションを実行し、結果を返す

    Args:
        crop_name (str): 作物名
        lat (float): 緯度
        lon (float): 経度

    Returns:
        float: シミュレーション結果(1haあたりの収量)
    """
    crop_variety = CropSimulation.crop_varieties[crop_name][0]
    soil_filename = "ec3.soil"
    coordinates = [lon, lat]
    simulation = CropSimulation(crop_name, crop_variety, coordinates, soil_filename)
    df = simulation.run_simulation()
    # 最終日のTAGPを取得
    print(df)
    result = df.loc[df.index[-1], "TWSO"]
    return result


# Example usage
if __name__ == "__main__":
    coordinates = [140.3819, 36.377]
    crop_name = "potato"
    lon, lat = coordinates
    result = run_simulation(crop_name, lat, lon)
    print(f"Simulation result: {result}")
