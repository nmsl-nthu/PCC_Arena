import os
import sys
from pyemd import emd_samples
import numpy as np
import subprocess as sp
import re
import logging
import argparse
from plyfile import PlyData, PlyElement


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

def evaluate(ori_path, bin_path, dec_path, log_path):
    ### acd, cd, cd-psnr, hausdorff ###
    pc_error = sp.run(['../../evaluator/geo_dist/build/pc_error',
                       '-a', ori_path, '-b', dec_path, '-d'], 
                       stdout=sp.PIPE, stderr=sp.DEVNULL, universal_newlines=True)
    for line in pc_error.stdout.splitlines():
        m = re.search('(?<=A->B,ACD1,p2point,).*', line)
        if (m):
            acd1_pt = m.group()
        m = re.search('(?<=A->B,ACD1,p2plane,).*', line)
        if (m):
            acd1_pl = m.group()
        m = re.search('(?<=B->A,ACD2,p2point,).*', line)
        if (m):
            acd2_pt = m.group()
        m = re.search('(?<=B->A,ACD2,p2plane,).*', line)
        if (m):
            acd2_pl = m.group()
        m = re.search('(?<=Symmetric,CD,p2point,).*', line)
        if (m):
            cd_pt = m.group()
        m = re.search('(?<=Symmetric,CD-PSNR,p2point,).*', line)
        if (m):
            cd_psnr_pt = m.group()
        m = re.search('(?<=Symmetric,CD,p2plane,).*', line)
        if (m):
            cd_pl = m.group()
        m = re.search('(?<=Symmetric,CD-PSNR,p2plane,).*', line)
        if (m):
            cd_psnr_pl = m.group()
        m = re.search('(?<=Symmetric,hF,p2point,).*', line)
        if (m):
            hausdorff_pt = m.group()
        m = re.search('(?<=Symmetric,hF,p2plane,).*', line)
        if (m):
            hausdorff_pl = m.group()

    ### EMD ###
    ori_ply = PlyData.read(ori_path)
    ori_pc = np.array([ori_ply['vertex']['x'], ori_ply['vertex']['y'], ori_ply['vertex']['z']]).transpose()
    ori_pc = np.expand_dims(ori_pc, axis=0)

    dec_ply = PlyData.read(dec_path)
    dec_pc = np.array([dec_ply['vertex']['x'], dec_ply['vertex']['y'], dec_ply['vertex']['z']]).transpose()
    dec_pc = np.expand_dims(dec_pc, axis=0)

    # check if the number of points are the same
    is_point_num_equal = bool(len(ori_ply['vertex']['x']) == len(dec_ply['vertex']['x']))
    if is_point_num_equal:
        emd = emd_samples(ori_pc, dec_pc)

    ### compressed file size ###
    ori_size = (os.stat(ori_path).st_size) / 1000 # kB
    bin_size = (os.stat(bin_path).st_size) / 1000 # kB
    compression_ratio = bin_size / ori_size # kB
    bpp = (bin_size * 1000 * 8) / len(ori_ply['vertex']['x']) # bits per points

    with open(log_path, 'a') as f:
        lines = [f'Point Cloud Compression Evaluation\n',
                 f'ply1: {ori_path}\n',
                 f'ply2: {dec_path}\n',
                 f'======================================\n',
                 f'ori_file size (kB)  : {ori_size}\n',
                 f'bin_file size (kB)  : {bin_size}\n',
                 f'compression ratio   : {compression_ratio}\n',
                 f'bpp (bits per point): {bpp}\n'
                 f'======================================\n',
                 f'Asym. Chamfer dist. (1->2) p2pt: {acd1_pt}\n',
                 f'Asym. Chamfer dist. (2->1) p2pt: {acd2_pt}\n',
                 f'Chamfer dist.              p2pt: {cd_pt}\n',
                 f'CD-PSNR                    p2pt: {cd_psnr_pt}\n',
                 f'Hausdorff distance         p2pt: {hausdorff_pt}\n',
                 f'======================================\n',
                 f'Asym. Chamfer dist. (1->2) p2pl: {acd1_pl}\n',
                 f'Asym. Chamfer dist. (2->1) p2pl: {acd2_pl}\n',
                 f'Chamfer dist.              p2pl: {cd_pl}\n',
                 f'CD-PSNR                    p2pl: {cd_psnr_pl}\n',
                 f'Hausdorff distance         p2pl: {hausdorff_pl}\n',
                 f'======================================\n']
        f.writelines(lines)
        if is_point_num_equal:
            f.write(f'Earth Mover\'s dist.            : {emd}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('ori_path', help='Path to ground turth point cloud')
    parser.add_argument('bin_path', help='Path to compressed bin_file')
    parser.add_argument('dec_path', help='Path to decompressed point cloud')
    parser.add_argument('log_path', help='Path to evaluation results log')

    args = parser.parse_args()

    assert os.path.exists(args.ori_path), f'{args.ori_path} does not exist'
    assert os.path.exists(args.dec_path), f'{args.dec_path} does not exist'
    assert not os.path.exists(args.log_path), f'{args.log_path} already exists'

    evaluate(args.ori_path, args.bin_path, args.dec_path, args.log_path)