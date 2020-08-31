# -*- coding: utf8 -*-

import argparse
import sys
from module_graph import ModuleNameTree, ErrorCollector, ModuleTree, detail, log

#  recuperer les id des data et les id des view, commencer par data
# récupérer les ids des .CSV, 1ere colonne = id, prendre avant la virgule
#  record -> récupérer id et module, en utilisant les ids de type module.id
#  a checker :
#  les fields ref="id"
#  les fields eval="[(4, ref('id
#  dans les .py
#  .browse_ref("id")
#  .ref("id")
#
#  à chaque fois, construire la référence préfixée et vérifier qu'elle est dans la liste
#
#  un dictionnaire d'id préfixés avec lien vers objets ID
#  un dictionnaire de modules avec lien vers objet module

#  parcourir les répertoires
#  si répertoire contient un manifest, c'est un module
#    charger le manifest, noter les dépendances (en chaine provisoirement)
#    noter le module, son chemin, ses dépendances, ses fichiers
#  sinon parcourir sous-répertoires
#

#  creation des objets modules :
#  pour chaque module :
#    pour chaque module dépendants
#       créer le module si pas existant
#       lier le module
#    initialiser le namespace = namespace des modules dépendants
#    parcourir les répertoires data/ et views/, dans l'ordre du manifeste créer les ids en notant le module
#    et le fichier
#    parcourir aussi .py, noter les reférence (module, nom complet fichier, id du record, n° ligne?,
#    texte de la référence, id cherché)
#    maj au fur et a mesure le namespace du module += id crées dans le module
#    vérifier présence des ref dans le namespace

#  quand tout les répertoires sont parcourus,
#    noter l'ordre des fichiers

#
# Struture :
#   ModuleNameTree contient la liste des ModuleInfo et fournit la fonction de scan de répertoire
#   ModuleInfo contient les info d'identification d'un module, et  une méthode de fabrication à partir d'un répertoire
#   ModuleTree contient le dictionnaire des module et la méthode récursive de vérification des modules (dépend de
#       ModuleNameTree
#
#  ErrorCollector gère la compilation et le stockage des erreurs rencontrées


def main(argv):
    global verbose
    global debug
    detail("starting... with argv %s" % argv)
    parser = argparse.ArgumentParser(
        description=u"Check xml ids validity in this directory")
    parser.add_argument(
        "directories",
        nargs='+',
        help=u"Directories to parse recursively")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-b",
        "--base",
        help="Base directory of odoo, to include in ids")
    group.add_argument(
        "-f",
        "--nobase",
        help=u"No base directory",
        action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    verbose = args.verbose
    debug = args.debug
    analyze(args.base, args.directories)


def analyze(base_dir, dirctrs):
    info_tree = ModuleNameTree()
    nb = 0
    if base_dir:
        log("scanning odoo base")
        nb = len(info_tree.scan_directory(base_dir))
        log("%s modules found" % nb)
    for dirctr in dirctrs:
        log("scanning %s" % dirctr)
        info_tree.scan_directory(dirctr)
    log("%s modules found" % (len(info_tree.mod_name_path) - nb))
    detail(map(lambda kv: "module %s, depends from %s" % (kv[0], kv[1].depends_name),
               info_tree.mod_name_path.iteritems()))
    error_collector = ErrorCollector()
    log("buiding module tree")
    mod = ModuleTree(
        error_collector=error_collector,
        depndcy_provider=info_tree)
    for name in info_tree.mod_name_path.keys():
        log("checking module %s" % name)
        mod.check(name)


def usage():
    print("\n USAGE\n -----")
    print("check_ids -b <directory of odoo base module> <directory to scan>")
    print("Option -f or --no-base allows to skip looking for base module")
    print("will check all xml ids declared in the directory ans sub-directories,"
          " taking into account manifest dependancies")
    print("reference to non existing ids will be signalled\n")


if __name__ == '__main__':
    main(sys.argv[1:])
    # main(['-d',  '-v' ,'-f',  '.'])
