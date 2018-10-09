import numpy as np
import cv2
import timeit

def perform_crop(img, gt, crop):
    cs = crop['crop_size']
    cropped_gt_img = img[crop['dim0'][0]:crop['dim0'][1], crop['dim1'][0]:crop['dim1'][1]]
    scaled_gt_img = cv2.resize(cropped_gt_img, (cs, cs), interpolation = cv2.INTER_CUBIC)
    scaled_gt = None
    if gt is not None:
        cropped_gt = gt[crop['dim0'][0]:crop['dim0'][1], crop['dim1'][0]:crop['dim1'][1]]
        scaled_gt = cv2.resize(cropped_gt, (cs, cs), interpolation = cv2.INTER_CUBIC)
        if len(scaled_gt.shape)==2:
            scaled_gt = scaled_gt[...,None]
    return scaled_gt_img, scaled_gt


def generate_random_crop(img, pixel_gt, line_gts, point_gts, params, bb_gt=None):
    
    contains_label = np.random.random() < params['prob_label'] if 'prob_label' in params else None
    cs = params['crop_size']

    cnt = 0
    while True:

        dim0 = np.random.randint(0,img.shape[0]-cs)
        dim1 = np.random.randint(0,img.shape[1]-cs)

        crop = {
            "dim0": [dim0, dim0+cs],
            "dim1": [dim1, dim1+cs],
            "crop_size": cs
        }
        hit=False
    
        if line_gts is not None:
            line_gt_match={}
            for name, gt in line_gts.items():
                ##tic=timeit.default_timer()
                line_gt_match[name] = np.zeros_like(gt)
                line_gt_match[name][...,0][gt[...,0] < dim1] = 1
                line_gt_match[name][...,0][gt[...,0] > dim1+cs] = 1

                line_gt_match[name][...,1][gt[...,1] < dim0] = 1
                line_gt_match[name][...,1][gt[...,1] > dim0+cs] = 1

                line_gt_match[name][...,2][gt[...,2] < dim1] = 1
                line_gt_match[name][...,2][gt[...,2] > dim1+cs] = 1

                line_gt_match[name][...,3][gt[...,3] < dim0] = 1
                line_gt_match[name][...,3][gt[...,3] > dim0+cs] = 1

                line_gt_match[name] = 1-line_gt_match[name]
                line_gt_match[name] = np.logical_and.reduce((line_gt_match[name][...,0], line_gt_match[name][...,1], line_gt_match[name][...,2], line_gt_match[name][...,3]))
                if line_gt_match[name].sum() > 0:
                    hit=True
        else:
            line_gt_match=None
        if bb_gt is not None:
            bb_gt_match=np.zeros_like(bb_gt)
            #TODO change to points instead of corners
            bb_gt_match[...,8][bb_gt[...,8] < dim1] = 1
            bb_gt_match[...,8][bb_gt[...,8] > dim1+cs] = 1

            bb_gt_match[...,9][bb_gt[...,9] < dim0] = 1
            bb_gt_match[...,9][bb_gt[...,9] > dim0+cs] = 1

            bb_gt_match[...,10][bb_gt[...,10] < dim1] = 1
            bb_gt_match[...,10][bb_gt[...,10] > dim1+cs] = 1

            bb_gt_match[...,11][bb_gt[...,11] < dim0] = 1
            bb_gt_match[...,11][bb_gt[...,11] > dim0+cs] = 1

            bb_gt_match[...,12][bb_gt[...,12] < dim1] = 1
            bb_gt_match[...,12][bb_gt[...,12] > dim1+cs] = 1

            bb_gt_match[...,13][bb_gt[...,13] < dim0] = 1
            bb_gt_match[...,13][bb_gt[...,13] > dim0+cs] = 1

            bb_gt_match[...,14][bb_gt[...,14] < dim1] = 1
            bb_gt_match[...,14][bb_gt[...,14] > dim1+cs] = 1

            bb_gt_match[...,15][bb_gt[...,15] < dim0] = 1
            bb_gt_match[...,15][bb_gt[...,15] > dim0+cs] = 1


            bb_gt_match = 1-bb_gt_match
            has_left= np.logical_and(bb_gt_match[...,8], bb_gt_match[...,9])
            has_right= np.logical_and(bb_gt_match[...,10], bb_gt_match[...,11]) 
            has_top= np.logical_and(bb_gt_match[...,12], bb_gt_match[...,13])  
            has_bot= np.logical_and(bb_gt_match[...,14], bb_gt_match[...,15])

            bb_gt_cornerCount = has_left+has_right+has_top+has_bot
            bb_gt_part = bb_gt_cornerCount==2 #if you have two corners in, your a partial
            bb_gt_candidate = np.logical_or( np.logical_and(np.logical_or(has_top,has_bot),np.logical_or(has_left,has_right)),
                                             np.logical_and(has_top,has_bot))

            #bb_gt_part -= bb_gt_fullin
            #we're going to edit bb_gt to make boxes partially in crop to be fully in crop 
            #bring in left side
            needs_left = np.logical_and(bb_gt_candidate,1-has_left)
            v_r = bb_gt[...,10:12]-bb_gt[...,8:10]
            dist1_l = (dim1-bb_gt[...,8])/v_r[...,0]
            dist1_r = (dim1+cs-bb_gt[...,8])/v_r[...,0]
            dist0_t = (dim0-bb_gt[...,9])/v_r[...,1]
            dist0_b = (dim0+cs-bb_gt[...,9])/v_r[..,1]
            mv_left = v_r*np.maximum(np.minimum.reduce([dist1_l,dist1_r,dist0_t,dist0_b]),0)
            bb_gt[...,0:2] = np.where( needs_left , bb_gt[...,0:2]+mv_left, bb_gt[...,0:2])
            bb_gt[...,6:7] = np.where( needs_left , bb_gt[...,6:7]+mv_left, bb_gt[...,6:7])

            #bring in right side
            needs_right = np.logical_and(bb_gt_candidate,1-has_right)
            v_l = -bb_gt[..,10:12]+bb_gt[..,8:10]
            dist1_l = (dim1-bb_gt[..,10])/v_l[..,0]
            dist1_r = (dim1+cs-bb_gt[..,10])/v_l[..,0]
            dist0_t = (dim0-bb_gt[..,11])/v_l[..,1]
            dist0_b = (dim0+cs-bb_gt[..,11])/v_l[..,1]
            mv_right = v_l*np.maximum(np.minimum.reduce([dist1_l,dist1_r,dist0_t,dist0_b]),0)
            bb_gt[...,2:4] = np.where( needs_right, bb_gt[...,2:4]+mv_right, bb_gt[...,2:4])
            bb_gt[...,4:6] = np.where( needs_right, bb_gt[...,4:6]+mv_right, bb_gt[...,4:6])

            if bb_gt_match.sum() > 0:
                hit=True
        else:
            bb_gt_match= None

        point_gt_match={}
        for name, gt in point_gts.items():
            ##tic=timeit.default_timer()
            point_gt_match[name] = np.zeros_like(gt)
            point_gt_match[name][...,0][gt[...,0] < dim1] = 1
            point_gt_match[name][...,0][gt[...,0] > dim1+cs] = 1

            point_gt_match[name][...,1][gt[...,1] < dim0] = 1
            point_gt_match[name][...,1][gt[...,1] > dim0+cs] = 1

            point_gt_match[name] = 1-point_gt_match[name]
            point_gt_match[name] = np.logical_and(point_gt_match[name][...,0], point_gt_match[name][...,1])
            if point_gt_match[name].sum() > 0:
                hit=True
            ##print('match: {}'.format(timeit.default_timer()-##tic))
        
        if (contains_label is None or
            (hit and contains_label or cnt > 100) or
            (not hit and not contains_label) ):
                cropped_gt_img, cropped_pixel_gt = perform_crop(img,pixel_gt, crop)
                if line_gts is not None:
                    for name in line_gts:
                        line_gt_match[name] = np.where(line_gt_match[name]!=0)
                if bb_gt is not None:
                    bb_gt = bb_gt[np.where(bb_gt_candidate)]
                for name in point_gts:
                    point_gt_match[name] = np.where(point_gt_match[name]!=0)
                return crop, cropped_gt_img, cropped_pixel_gt, line_gt_match, point_gt_match, bb_gt

        cnt += 1

class CropTransform(object):
    def __init__(self, crop_params):
        crop_size = crop_params['crop_size']
        self.random_crop_params = crop_params
        if 'pad' in crop_params:
            pad_by = crop_params['pad']
        else:
            pad_by = crop_size//2
        self.pad_params = ((pad_by,pad_by),(pad_by,pad_by),(0,0))

    def __call__(self, sample):
        org_img = sample['img']
        line_gts = sample['line_gt']
        point_gts = sample['point_gt']
        pixel_gt = sample['pixel_gt']

        #pad out to allow random samples to take space off of the page
        ##tic=timeit.default_timer()
        #org_img = np.pad(org_img, self.pad_params, 'mean')
        org_img = np.pad(org_img, self.pad_params, 'constant')
        if pixel_gt is not None:
            pixel_gt = np.pad(pixel_gt, self.pad_params, 'constant')
        ##print('pad: {}'.format(timeit.default_timer()-##tic))
        
        ##tic=timeit.default_timer()
        j=0
        #pad the points accordingly
        for name, gt in line_gts.items():
            #if np.isnan(gt).any():
            #    print('gt has nan, {}'.format(name))
            gt[:,:,0] = gt[:,:,0] + self.pad_params[0][0]
            gt[:,:,1] = gt[:,:,1] + self.pad_params[1][0]

            gt[:,:,2] = gt[:,:,2] + self.pad_params[0][0]
            gt[:,:,3] = gt[:,:,3] + self.pad_params[1][0]
        for name, gt in point_gts.items():
            gt[:,:,0] = gt[:,:,0] + self.pad_params[0][0]
            gt[:,:,1] = gt[:,:,1] + self.pad_params[1][0]

        crop_params, org_img, pixel_gt, line_gt_match, point_gt_match, _ = generate_random_crop(org_img, pixel_gt, line_gts, point_gts, self.random_crop_params)
        #print(crop_params)
        #print(gt_match)
        
        ##tic=timeit.default_timer()
        new_line_gts={}
        for name, gt in line_gts.items():
            gt = gt[line_gt_match[name]][None,...] #add batch dim (?)
            gt[...,0] = gt[...,0] - crop_params['dim1'][0]
            gt[...,1] = gt[...,1] - crop_params['dim0'][0]

            gt[...,2] = gt[...,2] - crop_params['dim1'][0]
            gt[...,3] = gt[...,3] - crop_params['dim0'][0]
            new_line_gts[name]=gt
        new_point_gts={}
        for name, gt in point_gts.items():
            gt = gt[point_gt_match[name]][None,...] #add batch dim (?)
            gt[...,0] = gt[...,0] - crop_params['dim1'][0]
            gt[...,1] = gt[...,1] - crop_params['dim0'][0]
            new_point_gts[name]=gt
        ##print('pad-minus: {}'.format(timeit.default_timer()-##tic))

            #if 'start' in name:
            #    for j in range(min(10,gt.size(1))):
            #        ##print('a {},{}   {},{}'.format(gt[:,j,0],gt[:,j,1],gt[:,j,2],gt[:,j,3]))

        return {
            "img": org_img,
            "line_gt": new_line_gts,
            "point_gt": new_point_gts,
            "pixel_gt": pixel_gt
        }
class CropBoxTransform(object):
    def __init__(self, crop_params):
        crop_size = crop_params['crop_size']
        self.random_crop_params = crop_params
        if 'pad' in crop_params:
            pad_by = crop_params['pad']
        else:
            pad_by = crop_size//2
        self.pad_params = ((pad_by,pad_by),(pad_by,pad_by),(0,0))

    def __call__(self, sample):
        org_img = sample['img']
        bb_gt = sample['bb_gt']
        point_gts = sample['point_gt']
        pixel_gt = sample['pixel_gt']

        #pad out to allow random samples to take space off of the page
        ##tic=timeit.default_timer()
        #org_img = np.pad(org_img, self.pad_params, 'mean')
        org_img = np.pad(org_img, self.pad_params, 'constant')
        if pixel_gt is not None:
            pixel_gt = np.pad(pixel_gt, self.pad_params, 'constant')
        ##print('pad: {}'.format(timeit.default_timer()-##tic))
        
        ##tic=timeit.default_timer()
        #corner points
        bb_gt[:,:,0] = bb_gt[:,:,0] + self.pad_params[0][0]
        bb_gt[:,:,1] = bb_gt[:,:,1] + self.pad_params[1][0]
        bb_gt[:,:,2] = bb_gt[:,:,2] + self.pad_params[0][0]
        bb_gt[:,:,3] = bb_gt[:,:,3] + self.pad_params[1][0]
        bb_gt[:,:,4] = bb_gt[:,:,4] + self.pad_params[0][0]
        bb_gt[:,:,5] = bb_gt[:,:,5] + self.pad_params[1][0]
        bb_gt[:,:,6 ] = bb_gt[:,:,6 ] + self.pad_params[0][0]
        bb_gt[:,:,7 ] = bb_gt[:,:,7 ] + self.pad_params[1][0]

        #cross/edge points
        bb_gt[:,:,8 ] = bb_gt[:,:,8 ] + self.pad_params[0][0]
        bb_gt[:,:,9 ] = bb_gt[:,:,9 ] + self.pad_params[1][0]
        bb_gt[:,:,10] = bb_gt[:,:,10] + self.pad_params[0][0]
        bb_gt[:,:,11] = bb_gt[:,:,11] + self.pad_params[1][0]
        bb_gt[:,:,12] = bb_gt[:,:,12] + self.pad_params[0][0]
        bb_gt[:,:,13] = bb_gt[:,:,13] + self.pad_params[1][0]
        bb_gt[:,:,14] = bb_gt[:,:,14] + self.pad_params[0][0]
        bb_gt[:,:,15] = bb_gt[:,:,15] + self.pad_params[1][0]

        for name, gt in point_gts.items():
            gt[:,:,0] = gt[:,:,0] + self.pad_params[0][0]
            gt[:,:,1] = gt[:,:,1] + self.pad_params[1][0]

        crop_params, org_img, pixel_gt, _, point_gt_match, new_bb_gt = generate_random_crop(org_img, pixel_gt, None, point_gts, self.random_crop_params, bb_gt=bb_gt)
        #print(crop_params)
        #print(gt_match)
        
        ##tic=timeit.default_timer()
        #new_bb_gt=bb_gt[bb_gt_match][None,...] #this is done in generate_random_crop() as it modified some bbs
        new_bb_gt=new_bb_gt[None,...] #this re-adds the batch dim
        new_bb_gt[...,0] = new_bb_gt[...,0] - crop_params['dim1'][0]
        new_bb_gt[...,1] = new_bb_gt[...,1] - crop_params['dim0'][0]
        new_bb_gt[...,2] = new_bb_gt[...,2] - crop_params['dim1'][0]
        new_bb_gt[...,3] = new_bb_gt[...,3] - crop_params['dim0'][0]
        new_bb_gt[...,4] = new_bb_gt[...,4] - crop_params['dim1'][0]
        new_bb_gt[...,5] = new_bb_gt[...,5] - crop_params['dim0'][0]
        new_bb_gt[...,6 ] = new_bb_gt[...,6 ] - crop_params['dim1'][0]
        new_bb_gt[...,7 ] = new_bb_gt[...,7 ] - crop_params['dim0'][0]
        #the cross/edge points are invalid now
        new_point_gts={}
        for name, gt in point_gts.items():
            gt = gt[point_gt_match[name]][None,...] #add batch dim (?)
            gt[...,0] = gt[...,0] - crop_params['dim1'][0]
            gt[...,1] = gt[...,1] - crop_params['dim0'][0]
            new_point_gts[name]=gt
        ##print('pad-minus: {}'.format(timeit.default_timer()-##tic))

            #if 'start' in name:
            #    for j in range(min(10,gt.size(1))):
            #        ##print('a {},{}   {},{}'.format(gt[:,j,0],gt[:,j,1],gt[:,j,2],gt[:,j,3]))

        return {
            "img": org_img,
            "bb_gt": new_bb_gt,
            "point_gt": new_point_gts,
            "pixel_gt": pixel_gt
        }
