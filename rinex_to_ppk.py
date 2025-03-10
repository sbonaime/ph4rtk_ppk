#!/usr/bin/env python3
# pylint: disable=no-member

import sys
from argparse import ArgumentParser, FileType, RawDescriptionHelpFormatter
from dataclasses import dataclass
from os.path import basename
import csv
from math import radians, cos
import numpy as np
from io import StringIO
from pathlib import Path


DEGREE_LAT_IN_METERS = 10000000/90



@dataclass
class PpkTimestamp:
    """Calculate position from ppk timestamp"""

    index: str
    time: float
    northing: str
    easting: str
    elevation: str
    ph4_base_file: str

    def calculate_values(self, pos_data_float, file_index):
        northing_diff = float(self.northing.strip().split(',', maxsplit=1)[0])
        easting_diff = float(self.easting.strip().split(',', maxsplit=1)[0])
        elevation_diff = float(self.elevation.strip().split(',', maxsplit=1)[0])

        inf = False
        sup = False

        # Find nearest Timestamp
        for idx, line in enumerate(pos_data_float):
            if float(line[1]) > self.time:
                inf = pos_data_float[idx-1]
                sup = pos_data_float[idx]
                break

        if type(inf) == bool or type(sup) == bool:
            print("############################")
            print(f"No timestamp for {self.ph4_base_file}_{file_index:0>4}.JPG")
            return

        percent_diff_between_timestamps = (self.time - inf[1])/(sup[1]-inf[1])
        interpolated_lat = (
            inf[2]*(1-percent_diff_between_timestamps)+sup[2]*percent_diff_between_timestamps)
        interpolated_lon = (
            inf[3]*(1-percent_diff_between_timestamps)+sup[3]*percent_diff_between_timestamps)
        interpolated_alti = (
            inf[4]*(1-percent_diff_between_timestamps)+sup[4]*percent_diff_between_timestamps)

        degree_lon_in_meters = DEGREE_LAT_IN_METERS*cos(radians(inf[2]))

        lat_diff_deg = northing_diff / 1000 / DEGREE_LAT_IN_METERS
        lon_diff_deg = easting_diff / 1000 / degree_lon_in_meters
        alti_diff = elevation_diff / 1000

        new_lat = interpolated_lat + lat_diff_deg
        new_lon = interpolated_lon + lon_diff_deg
        new_alt = interpolated_alti - alti_diff
        print(f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lon}\t{new_lat}\t{new_alt}')
        return f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lon}\t{new_lat}\t{new_alt}\n'


@dataclass
class RinexToPpk:
    """Import calculated RINEX from PH4RTK with images date and find accurate PPK positions"""
    data_dir: Path
    odm : bool
    delimiter : str
    output_path : Path

    def __post_init__(self):
        if not self.data_dir.exists() :
            print('self.data_dir does not exsits')
            sys.exit()

        if not list(self.data_dir.rglob('*Rinex.pos')):
            print(f"Rinex.pos file not found in {self.data_dir}")
            sys.exit()
        self.pos_ph4_rinex_file = list(self.data_dir.rglob('*Rinex.pos'))[0]

        if not list(self.data_dir.rglob('*_Timestamp.MRK')):
            print(f"Timestamp.MRK file not found in {self.data_dir}")
            sys.exit()

        self.timestamp_file = list(self.data_dir.rglob('*_Timestamp.MRK'))[0]

        # print(f'{self.pos_ph4_rinex_file=}\t{self.timestamp_file}')
        # sys.exit()

    def calculate_ppk_positions(self):
        """Calculate position from ppk data"""
        #        __import__("IPython").embed()
        #        sys.exit()
        with self.pos_ph4_rinex_file.open(mode="r", encoding="utf-8")  as rinex_file:

            # skip headers
            tout = rinex_file.readlines()
            output =""

            for line in tout:
                if not '%' in line:
                    output+=line

            pos_data = list(csv.reader(output.splitlines(), delimiter=self.delimiter))
            pos_data_float = np.asarray(pos_data, dtype=float)

        ph4_part_a,ph4_part_b,_ = basename(self.timestamp_file.name).split('_')

        ph4_base_file=f'{ph4_part_a}_{ph4_part_b}'
        output_file= self.output_path.cwd() / f'{ph4_part_a}_{ph4_part_b}_PPK.csv'
        file_index = 1

        with output_file.open(mode="w", encoding="utf-8") as output_csv:
            self.odm and output_csv.write("EPSG:4326\n")
            with self.timestamp_file.open(mode="r", encoding="utf-8")  as timestamp_file:
                for line in timestamp_file:
                    index, time, day_number, northing, easting, elevation, _, _, _, _, _ = line.split('\t')

                    result = PpkTimestamp(index, float(time), northing, easting, elevation, ph4_base_file).calculate_values(pos_data_float, file_index)
                    if result :
                        output_csv.write(result)
                    file_index = file_index+1




def parse_arguments():
    parser = ArgumentParser(prog='RinexRoPPK',
        formatter_class=RawDescriptionHelpFormatter,
        description='''Convert rinex file form RTKPOST and timestamp.MRK from PH4RTK
        to csv file for opendronemap
        ''')

    parser.add_argument(
        '--data_dir', '-r', type=str,
        metavar='PATH',required=True,
        help="Data input directory with RTKPOST data as 100_0138_Rinex.pos and 100_0138_Timestamp.MRK")

    parser.add_argument(
        '--delimiter', '-d', type=str, required=False, default=',',
        help="Char delimiter of the Rinex")

    parser.add_argument('--odm', action='store_true',
                    help='output with EPSG:4326 header for ODM')

    parser.add_argument('--output_path','-o',  type=str, required=False,
                    help='output path to write PPK.csv data')
    # parser.add_argument(
    #     '--output', '-o', type=FileType('w'), default=sys.stdout,
    #     metavar='PATH',
    #     help="Output file (default: standard output)")
    # parser.add_argument(
    #     '--separator', '-s', type=str, default='@@', metavar='STR',
    #     help="Separator between non-final subword units (default: '%(default)s'))")

    return parser


def main():
    arguments=parse_arguments()
    args=arguments.parse_args()

    if len(args.delimiter) > 1 :
        print("Delimiter is just one char like ',' or ' '")
        sys.exit()
    if not args.output_path :
        args.output_path=args.data_dir

    rinextoppk = RinexToPpk(Path(args.data_dir),args.odm, args.delimiter,Path(args.output_path))
    rinextoppk.calculate_ppk_positions()


if __name__ == "__main__":
    main()
