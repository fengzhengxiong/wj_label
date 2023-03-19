

import numpy as np

import cv2



class CameraMap(object):
    Param = {
        'intrinsics': [1147.9, 1143.4, 951.6894, 566.33],
        'rotate': [2.02308903, 0.12832518, -0.10520086],
        'translation': [95.262/1000, 164.969/1000, 15.345/1000],
        'distortion': [-0.3341, 0.1085, 0.000413, 0.00070638, 0],
    }

    def __init__(self):

        self.fx = 1147.9
        self.fy = 1143.4
        self.cx = 951.6894
        self.cy = 566.33

        '''内参camera intrinsics
        fx  0   cx
        0   fy  cy
        0   0   1
        '''
        self.intrinsics = np.mat([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1.0]])
        '''外参camera extrinsics
        R|T
        '''
        self.rotate_vec = np.mat([2.02308903, 0.12832518, -0.10520086])
        self.translation_vec = np.mat([95.262, 164.969, 15.345]) / 1000
        '''畸变系数 distortion_coefficients
        径向k1 k2 k3 ，切向畸变 p1 p2
        '''
        self.distortion = np.mat([-0.3341, 0.1085, 0.000413, 0.00070638, 0])

        self.extrinsics = self.getExtrinsicsMatrix()

    def setParam(self, param: dict):
        self.fx, self.fy, self.cx, self.cy = param.get('intrinsics', [1147.9, 1143.4, 951.6894, 566.33])
        rotate = param.get('rotate', [2.02308903, 0.12832518, -0.10520086])
        self.rotate_vec = np.mat(rotate)
        translation = param.get('translation', [95.262/1000, 164.969/1000, 15.345/1000])
        self.translation_vec = np.mat(translation)
        distortion = param.get('param', [-0.3341, 0.1085, 0.000413, 0.00070638, 0])
        self.distortion = np.mat(distortion)
        self.extrinsics = self.getExtrinsicsMatrix()

    def getExtrinsicsMatrix(self):
        """
        计算外参
        :return:
        """
        extrinsics = np.zeros((4, 4))
        rotate_mat, _ = cv2.Rodrigues(self.rotate_vec)  # 旋转向量和旋转矩阵的互相转换
        extrinsics[:3, :3] = rotate_mat
        extrinsics[:3, 3] = self.translation_vec
        extrinsics[3, 3] = 1.0
        return extrinsics

    def lidar_to_cam(self, xyz_lidar):
        xyz_lidar = xyz_lidar
        xyz_lidar = np.hstack([xyz_lidar, np.ones(xyz_lidar.shape[0]).reshape(-1, 1)])

        return self.extrinsics.dot(xyz_lidar.T)[:3].T


    def lidar_to_pixel(self, xyz_lidar):
        xyz_cam = self.lidar_to_cam(xyz_lidar)
        filter_cam = np.where(xyz_cam[:, 2] > 0, True, False)

        lidar_data = np.mat(xyz_lidar)
        point_2d, _ = cv2.projectPoints(np.array(lidar_data), np.array(self.rotate_vec),
                                        np.array(self.translation_vec), np.array(self.intrinsics),
                                        np.array(self.distortion))
        point_2d = np.squeeze(point_2d)
        return point_2d


def main():

    cam = CameraMap()

    param = {
        'intrinsics': [1166.85, 1161.06, 979.518, 539.0],
        'rotate': [1.081377707240168, 1.9341321416221342, -1.3920648620145197],
        'translation': np.mat([231.71811100000002, 341.47311, -38.183171])/1000,
        'distortion': [-0.33096, 0.10432, 0.000007, -0.00065, 0],
    }

    param = {
        'intrinsics': [1178.2835438239, 1173.81249389131, 975.647602101858, 577.579850541188],
        'rotate': [1.4385203413447092, 1.197874358314993, -0.9756231053181874],
        'translation': np.mat([-5316.78, 1310.178, 247.882]) / 1000,
        'distortion': [-0.336948354, 0.10183373794, 0.000528904, 0.0001445108, 0],
    }



    cam.setParam(param)

    points = [
        [-50.12230993, 5.3744946, -1.80837],
        [-50.12230993, 5.3744946, -5.02579],
    ]

    points = np.mat(points)

    po2d = cam.lidar_to_pixel(points)

    print(po2d)
    print(po2d.tolist())


if __name__ == '__main__':
    # check_csv_image()#点云标注框投影到图像
    # check_points_images()#点云原始数据投影到图像

    main()

