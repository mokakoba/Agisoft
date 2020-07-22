import os
import Metashape

def autoscan():
    # File Setup
    doc = Metashape.app.document
    file_path = Metashape.app.getExistingDirectory()
    project_path = Metashape.app.getSaveFileName("File name and location for saving:")
    
    if not project_path:
	    print("Booting Down")
    if project_path[-4:].lower() != ".psz":
	    project_path += ".psz"
	    
    path_photos = Metashape.app.getExistingDirectory("Location of Photos:")
    path_photos += "//"
    
    #Creating New Chunk
    chunk = doc.addChunk()

    #List of images from path
    image_list =[
	    path.join(path_photos, path)
	    for path in listdir(path_photos)
	    if path.lower().endswith(("jpg", "jpeg", "tif", "png","JPG","JPEG","TIF",""))
	    ]

    #Add photos to chunk
    chunk.addPhotos(image_list)

    ##chunk.detectMarkers() #Aruco Marker

    #Disables images that are less than 0.5 quality(recommended by agisoft)
    chunk.estimateImageQuality()

    for i in range(0, len(chunk.cameras)):
        camera = chunk.cameras[i]
        quality = camera.frames[0].meta["Image/Quality"]
        if float(quality) < 0.5:
            camera.enabled = False

    #Aligns all the photos
    chunk.matchPhotos(
        downscale=1
        generic_preselection=True,
        reference_preselection=True,
        keypoint_limit=60000,
        tiepoint_limit=4000)
    chunk.alignCameras(adaptive_fitting=True)
    doc.save()

    # Optimize Cameras
    chunk.optimizeCameras(
        fit_f=True,
        fit_cx=True,
        fit_cy=True,
        fit_b1=True,
        fit_b2=False,
        fit_k1=True,
        fit_k2=True,
        fit_k3=True,
        fit_k4=False,
        fit_p1=True,
        fit_p2=True,
        fit_p3=False,
        fit_p4=False,
        )   
    doc.save()

    #Adjusts the ReconstructionUncertainty
    f = Metashape.PointCloud.Filter()
    f.init(chunk, criterion=Metashape.PointCloud.Filter.ReconstructionUncertainty)
##    f.removePoints(100)
##    f.removePoints(75)
##    f.removePoints(50)
##    f.removePoints(45)
##    f.removePoints(40)
    f.removePoints(35)

    chunk.optimizeCameras(
        fit_f=True,
        fit_cx=True,
        fit_cy=True,
        fit_b1=True,
        fit_b2=True,
        fit_k1=True,
        fit_k2=True,
        fit_k3=True,
        fit_k4=True,
        fit_p1=True,
        fit_p2=True,
        fit_p3=False,
        fit_p4=False,
        )
    doc.save()

    #Adjusts the ProjectionAccuracy
    f.init(chunk, criterion=Metashape.PointCloud.Filter.ProjectionAccuracy)
    f.removePoints(3)
##    f.removePoints(2.8)
##    f.removePoints(2.5)
##    f.removePoints(2.3)

    #sets tiepoint accuracy to 0.1
    chunk.tiepoint_accuracy = 0.1

    chunk.optimizeCameras(
        fit_f=True,
        fit_cx=True,
        fit_cy=True,
        fit_b1=True,
        fit_b2=True,
        fit_k1=True,
        fit_k2=True,
        fit_k3=True,
        fit_k4=True,
        fit_p1=True,
        fit_p2=True,
        fit_p3=True,
        fit_p4=True,
        )   

    #Adjusts the Reprojection Error
    f.init(chunk, criterion=Metashape.PointCloud.Filter.ReprojectionError)
    f.removePoints(0.5)
##    f.removePoints(0.4)
##    f.removePoints(0.3)

    chunk.optimizeCameras(
        fit_f=True,
        fit_cx=True,
        fit_cy=True,
        fit_b1=True,
        fit_b2=True,
        fit_k1=True,
        fit_k2=True,
        fit_k3=True,
        fit_k4=True,
        fit_p1=True,
        fit_p2=True,
        fit_p3=True,
        fit_p4=True,
    )
    doc.save()

    #Builds the DenseCloud
    chunk.buildDepthMaps(downscale=4, filter=Metashape.AggressiveFiltering)
    chunk.buildDenseCloud()
    doc.save()
	
    #build mesh
    chunk.buildModel(surface_type=Arbitrary, face_count_custom=200000)

    #save
    doc.save(path = project_path)
    Metashape.app.update()

    #export
    chunk.exportModel(path = project_path + ".obj", texture_format = Metashape.ImageFormatPNG, format = Metashape.ModelFormatOBJ)

autoscan()
