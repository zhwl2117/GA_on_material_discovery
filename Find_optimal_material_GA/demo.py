from GA import GenePopulation


file = ''
heteroatom_list = ['B', 'N']
epochs = 10
percents = [0.6, 0.2, 0.1, 0.1]

if __name__ == '__main__':
    gene_population = GenePopulation(file, heteroatom_list, epochs, percents)
    gene_population.iterate()
