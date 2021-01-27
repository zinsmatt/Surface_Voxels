#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Matthieu Zins
"""

import trimesh
import numpy as np
import os
import argparse

"""
    ======   Voxelize the surface of a mesh   ======
"""



def create_if_needed(folder):
    if not os.path.isdir(folder):
        os.mkdir(folder)



parser = argparse.ArgumentParser(description='Pass object name')
parser.add_argument('input_mesh', type=str)
parser.add_argument('--output_folder', type=str, default="")
parser.add_argument('--resolution', type=int, nargs=3, default=[50, 50, 50], 
                    help="resolution_X resolution_Y resolution_Z")
parser.add_argument('--sampling', type=int, default="100000",
                    help="number of points sampled on the mesh")
args = parser.parse_args()


input_mesh_filename = args.input_mesh
object_name = os.path.splitext(os.path.basename(input_mesh_filename))[0]
output_folder = args.output_folder
if len(output_folder) == 0: output_folder = object_name
RES_X, RES_Y, RES_Z = args.resolution
sample_points_count = args.sampling

create_if_needed(output_folder)


mesh = trimesh.exchange.load.load(input_mesh_filename)


# Uniform Points Sampling
pts, _ = trimesh.sample.sample_surface_even(mesh, sample_points_count )

# Save sample points
sampled_points_mesh = trimesh.Trimesh(vertices=pts)
sampled_points_mesh.export(os.path.join(output_folder, object_name + "_resampled_points.ply"))


# Adjust the grid origin and voxels size
origin = pts.min(axis=0)
dimensions = pts.max(axis=0) - pts.min(axis=0)
scales = np.divide(dimensions, np.array([RES_X-1, RES_Y-1, RES_Z-1]))
scale = np.max(scales)


# Voxelize

pts -= origin
pts /= scale
pts_int = np.round(pts).astype(int)

grid = np.zeros((RES_X, RES_Y, RES_Z), dtype=int)
gooRES_X = np.where(np.logical_and(pts_int[:, 0] >= 0, pts_int[:, 0] < RES_X))[0]
gooRES_Y = np.where(np.logical_and(pts_int[:, 1] >= 0, pts_int[:, 1] < RES_Y))[0]
gooRES_Z = np.where(np.logical_and(pts_int[:, 2] >= 0, pts_int[:, 2] < RES_Z))[0]
goods = np.intersect1d(np.intersect1d(gooRES_X, gooRES_Y), gooRES_Z)
pts_int = pts_int[goods, :]
grid[pts_int[:, 0], pts_int[:, 1], pts_int[:, 2]] = 1




# Save voxels
voxel_pts = np.array([[-0.5, 0.5, -0.5],
                      [0.5, 0.5, -0.5],
                      [0.5, 0.5, 0.5],
                      [-0.5, 0.5, 0.5],
                      [-0.5, -0.5, -0.5],
                      [0.5, -0.5, -0.5],
                      [0.5, -0.5, 0.5],
                      [-0.5, -0.5, 0.5]])
voxel_faces = np.array([[0, 1, 2, 3],
                        [1, 5, 6, 2],
                        [5, 4, 7, 6],
                        [4, 0, 3, 7],
                        [0, 4, 5, 1],
                        [7, 3, 2, 6]])

def get_voxel(i, j, k):
    global voxel_pts, voxel_faces
    v = np.array([i, j, k], dtype=float) * scale
    v += origin
    points = voxel_pts * scale + v
    return points, voxel_faces.copy()

points = []
faces = []
fi = 0
for i in range(RES_X):
    for j in range(RES_Y):
        for k in range(RES_Z):
            if grid[i, j, k]:
                p, f = get_voxel(i, j, k)
                points.append(p)
                f += fi
                faces.append(f)
                fi += 8

points = np.vstack(points)
faces = np.vstack(faces)
# Write obj mesh with quad faces
with open(os.path.join(output_folder, object_name + "_voxels.obj"), "w") as fout:
    for p in points:fout.write("v " + " ".join(map(str, p)) + "\n")
    for f in faces+1:fout.write("f " + " ".join(map(str, f)) + "\n")


print(object_name, "done.")