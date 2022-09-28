from datetime import datetime
from uuid import uuid4
import json
from base64 import b64decode
import re

from hyperspace.murd import mddb, murd
from hyperspace.objects import HyperBounty, asdict
from hyperspace.utilities import get_html_template, process_multipart_form_submission
import hyperspace.ses as ses
import hyperspace.s3 as s3
import hyperspace.stlToImageLambda as stlToImageLambda
from hyperspace.bounty_system.render_bounties import render_bounty


def generateReferenceImageForSTLs(bounty: HyperBounty):
    # For each STL in reference material, request an image from solidpoly.stl_to_image
    altered = False
    for refMat in bounty.ReferenceMaterial:
        if bounty.get_filetype(refMat) == 'stl':
            refMatName = refMat[:-4]
            refImageName = f"STLToImage_{refMatName}.png"
            kwargs = {
                "stlPath": bounty.image_path(refMat)[1:],
                "outputFile": bounty.image_path(refImageName)[1:]
            }
            stlToImageLambda.stlToImage(**kwargs)
            bounty.ReferenceMaterial.append(refImageName)
            bounty.ReferenceMaterial = list(set(bounty.ReferenceMaterial))
            altered = True
    if altered:
        bounty.set()


def centerSTLDimensions(bounty: HyperBounty):
    # For each STL in reference material, provide positioning information to center model in AFrame viewer
    altered = False
    newReferenceMaterial = []
    for refMat in bounty.ReferenceMaterial:
        if bounty.get_filetype(refMat) == 'stl':
            existingInfo = re.search(stlToImageLambda.stlPositionPattern, refMat)
            if existingInfo:
                refMatName = refMat[:-len(existingInfo.group())]
            else:
                refMatName = refMat[:-4]

            mods = stlToImageLambda.stlCenteringDimensions(
                bounty.image_path(refMat)[1:])

            newRefMatName = f"{refMatName}_stlposition_{mods['xmod']:.2f}x{mods['ymod']:.2f}x{mods['zmod']:.2f}.stl"
            newRefMatPath = bounty.image_path(newRefMatName)[1:]

            newReferenceMaterial.append(newRefMatName)
            s3.renamePublic(bounty.image_path(refMat)[1:], newRefMatPath)
            altered = True
        else:
            newReferenceMaterial.append(refMat)

    if altered:
        bounty.ReferenceMaterial = newReferenceMaterial
        bounty.set()



def approve_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    return 200, {}


def reject_bounty(event):
    bounty_id = unquote_plus(event['pathParameters']['bounty_id'])
    bounty = HyperBounty.retrieve(bounty_id)
    return 200, {}
